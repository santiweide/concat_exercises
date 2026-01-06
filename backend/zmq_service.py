"""
ZeroMQ messaging layer for inter-service communication.
"""
import asyncio
import json
import uuid
from typing import Any, Callable, Awaitable
from dataclasses import dataclass
import zmq
import zmq.asyncio
import structlog

logger = structlog.get_logger()


@dataclass
class ZMQMessage:
    """ZeroMQ message wrapper."""
    id: str
    action: str
    payload: dict
    
    def to_json(self) -> bytes:
        return json.dumps({
            "id": self.id,
            "action": self.action,
            "payload": self.payload
        }).encode('utf-8')
    
    @classmethod
    def from_json(cls, data: bytes) -> "ZMQMessage":
        obj = json.loads(data.decode('utf-8'))
        return cls(
            id=obj.get("id", ""),
            action=obj.get("action", ""),
            payload=obj.get("payload", {})
        )


@dataclass
class ZMQResponse:
    """ZeroMQ response wrapper."""
    id: str
    success: bool
    data: dict
    error: str | None = None
    
    def to_json(self) -> bytes:
        return json.dumps({
            "id": self.id,
            "success": self.success,
            "data": self.data,
            "error": self.error
        }).encode('utf-8')
    
    @classmethod
    def from_json(cls, data: bytes) -> "ZMQResponse":
        obj = json.loads(data.decode('utf-8'))
        return cls(
            id=obj.get("id", ""),
            success=obj.get("success", False),
            data=obj.get("data", {}),
            error=obj.get("error")
        )


class ZMQServiceServer:
    """ZeroMQ service server (REP socket)."""
    
    def __init__(self, address: str, name: str = "service"):
        self.address = address
        self.name = name
        self.context = zmq.asyncio.Context()
        self.socket: zmq.asyncio.Socket | None = None
        self.handlers: dict[str, Callable[[dict], Awaitable[dict]]] = {}
        self._running = False
    
    def register(self, action: str, handler: Callable[[dict], Awaitable[dict]]):
        """Register a handler for an action."""
        self.handlers[action] = handler
        logger.info(f"Registered handler", service=self.name, action=action)
    
    async def start(self):
        """Start the service server."""
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(self.address)
        self._running = True
        logger.info(f"ZMQ service started", service=self.name, address=self.address)
        
        while self._running:
            try:
                data = await self.socket.recv()
                message = ZMQMessage.from_json(data)
                
                logger.debug("Received message", service=self.name, action=message.action, id=message.id)
                
                handler = self.handlers.get(message.action)
                if handler:
                    try:
                        result = await handler(message.payload)
                        response = ZMQResponse(id=message.id, success=True, data=result)
                    except Exception as e:
                        logger.error("Handler error", service=self.name, action=message.action, error=str(e))
                        response = ZMQResponse(id=message.id, success=False, data={}, error=str(e))
                else:
                    response = ZMQResponse(
                        id=message.id, 
                        success=False, 
                        data={}, 
                        error=f"Unknown action: {message.action}"
                    )
                
                await self.socket.send(response.to_json())
            except zmq.ZMQError as e:
                if self._running:
                    logger.error("ZMQ error", service=self.name, error=str(e))
            except Exception as e:
                logger.error("Unexpected error", service=self.name, error=str(e))
    
    async def stop(self):
        """Stop the service server."""
        self._running = False
        if self.socket:
            self.socket.close()
        self.context.term()
        logger.info(f"ZMQ service stopped", service=self.name)


class ZMQServiceClient:
    """ZeroMQ service client (REQ socket)."""
    
    def __init__(self, address: str, name: str = "client"):
        self.address = address
        self.name = name
        self.context = zmq.asyncio.Context()
        self.socket: zmq.asyncio.Socket | None = None
        self._lock = asyncio.Lock()
    
    async def connect(self):
        """Connect to the service."""
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(self.address)
        logger.info(f"ZMQ client connected", client=self.name, address=self.address)
    
    async def call(self, action: str, payload: dict, timeout: float = 30.0) -> dict:
        """Call a service action."""
        if not self.socket:
            await self.connect()
        
        message = ZMQMessage(
            id=str(uuid.uuid4()),
            action=action,
            payload=payload
        )
        
        async with self._lock:
            await self.socket.send(message.to_json())
            
            # Wait for response with timeout
            if await self.socket.poll(timeout=int(timeout * 1000)):
                data = await self.socket.recv()
                response = ZMQResponse.from_json(data)
                
                if response.success:
                    return response.data
                else:
                    raise Exception(response.error or "Unknown error")
            else:
                raise TimeoutError(f"Request timed out after {timeout}s")
    
    async def close(self):
        """Close the client connection."""
        if self.socket:
            self.socket.close()
        self.context.term()
        logger.info(f"ZMQ client closed", client=self.name)


# Global clients for HTTP handlers to use
question_client: ZMQServiceClient | None = None
queue_client: ZMQServiceClient | None = None


async def init_clients(question_addr: str, queue_addr: str):
    """Initialize ZMQ clients."""
    global question_client, queue_client
    
    question_client = ZMQServiceClient(question_addr, "question-client")
    await question_client.connect()
    
    queue_client = ZMQServiceClient(queue_addr, "queue-client")
    await queue_client.connect()


async def close_clients():
    """Close ZMQ clients."""
    global question_client, queue_client
    
    if question_client:
        await question_client.close()
    if queue_client:
        await queue_client.close()
