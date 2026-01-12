#!/usr/bin/env python3
"""
测试队列加载功能
用于验证队列中的题目是否能正确加载
"""
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from storage import question_store, queue_store

def test_queue_loading():
    """测试队列加载"""
    print("=" * 60)
    print("测试队列加载功能")
    print("=" * 60)
    
    # 获取所有队列
    all_queues = list(queue_store.queues.values())
    print(f"\n总共有 {len(all_queues)} 个队列\n")
    
    for queue in all_queues:
        print(f"队列ID: {queue.id}")
        print(f"队列名称: {queue.name}")
        print(f"题目ID列表: {queue.questionIds}")
        print(f"题目数量: {len(queue.questionIds)}")
        
        # 尝试加载队列详情
        queue_detail = queue_store.get(queue.id)
        if queue_detail:
            print(f"实际加载的题目数量: {len(queue_detail.questions)}")
            
            # 检查哪些题目加载失败
            loaded_ids = {q.id for q in queue_detail.questions}
            missing_ids = set(queue.questionIds) - loaded_ids
            
            if missing_ids:
                print(f"⚠️  警告: 以下题目ID在队列中但未能加载:")
                for qid in missing_ids:
                    question = question_store.questions.get(qid)
                    if question:
                        is_deleted = getattr(question, 'deleted', False)
                        print(f"  - {qid}: {'已删除' if is_deleted else '存在但未加载'}")
                    else:
                        print(f"  - {qid}: 不存在")
            else:
                print("✓ 所有题目都成功加载")
        else:
            print("✗ 无法加载队列详情")
        
        print("-" * 60)

def test_deleted_questions():
    """检查已删除的题目"""
    print("\n" + "=" * 60)
    print("检查已删除的题目")
    print("=" * 60 + "\n")
    
    deleted_questions = [q for q in question_store.questions.values() 
                        if getattr(q, 'deleted', False)]
    
    print(f"总共有 {len(deleted_questions)} 个已删除的题目:\n")
    
    for q in deleted_questions:
        print(f"题目ID: {q.id}")
        print(f"标题: {q.title}")
        print(f"删除时间: {q.deletedAt}")
        
        # 检查这个题目是否在某个队列中
        in_queues = []
        for queue in queue_store.queues.values():
            if q.id in queue.questionIds:
                in_queues.append(queue.name)
        
        if in_queues:
            print(f"⚠️  此题目仍在以下队列中: {', '.join(in_queues)}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_queue_loading()
    test_deleted_questions()
