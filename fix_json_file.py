import json
import re
import os
from collections import defaultdict

def fix_consecutive_speakers_and_empty(file_path, output_path=None):
    if output_path is None:
        output_path = file_path.replace('.json', '_fixed.json')
    
    print(f"正在处理文件: {file_path}")
    print(f"修复后的文件将保存为: {output_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.loads(file.read())
        
        # 统计信息
        total_conversations = len(data)
        total_fixed = 0
        total_empty_removed = 0
        total_system_removed = 0
        total_speaker_renamed = 0
        total_no_num_tokens_removed = 0
        total_bing_bard_removed = 0
        fixed_items = defaultdict(int)
        empty_removed_items = defaultdict(int)
        system_removed_items = defaultdict(int)
        speaker_renamed_items = defaultdict(int)
        no_num_tokens_removed_items = []
        bing_bard_removed_items = []
        
        # 过滤后的数据列表
        filtered_data = []
        
        for item in data:
            if "conversations" not in item:
                filtered_data.append(item)
                continue
            
            conversations = item["conversations"]
            item_id = item.get("id", "unknown")
            
            # 检查是否有任何 gpt 对话缺少 num_tokens 字段
            should_remove_item = False
            for conv in conversations:
                if conv.get("from") == "gpt" and "num_tokens" not in conv:
                    should_remove_item = True
                    break
            
            if should_remove_item:
                total_no_num_tokens_removed += 1
                no_num_tokens_removed_items.append(item_id)
                continue  # 跳过这整个对话项，不添加到 filtered_data
            
            # 检查是否有任何对话包含 bing/bard/chatgpt 发言者
            has_bing_bard_chatgpt = False
            for conv in conversations:
                if conv.get("from") in ["bing", "bard", "chatgpt"]:
                    has_bing_bard_chatgpt = True
                    break
            
            if has_bing_bard_chatgpt:
                total_bing_bard_removed += 1
                bing_bard_removed_items.append(item_id)
                continue  # 跳过这整个对话项，不添加到 filtered_data
            
            # 如果通过了 num_tokens 检查，继续处理其他问题
            
            # 第一步：删除空的对话条目
            non_empty_conversations = []
            
            for conv in conversations:
                # 检查是否为空对话（value为空字符串或只有空白字符）
                value = conv.get("value", "").strip()
                if value == "":
                    total_empty_removed += 1
                    empty_removed_items[item_id] += 1
                else:
                    non_empty_conversations.append(conv)
            
            conversations = non_empty_conversations
            
            # 第二步：删除 system 发言者的对话条目
            non_system_conversations = []
            
            for conv in conversations:
                speaker = conv.get("from", "")
                if speaker == "system":
                    total_system_removed += 1
                    system_removed_items[item_id] += 1
                else:
                    non_system_conversations.append(conv)
            
            conversations = non_system_conversations
            
            # 第三步：由于已经在前面过滤掉了包含 bing/bard/chatgpt 的对话，这里不需要重命名
            
            # 第四步：处理连续相同发言者
            fixed_conversations = []
            prev_speaker = None
            
            for conv in conversations:
                current_speaker = conv.get("from", "")
                
                # 如果当前发言者与前一个相同，跳过这条消息
                if prev_speaker == current_speaker and (current_speaker == "human" or current_speaker == "gpt"):
                    fixed_items[item_id] += 1
                    total_fixed += 1
                    continue
                
                # 保留这条消息
                fixed_conversations.append(conv)
                prev_speaker = current_speaker
            
            # 更新对话
            item["conversations"] = fixed_conversations
            
            # 更新 num_round（使用修复后的对话数量）
            if "num_round" in item:
                item["num_round"] = len(fixed_conversations)
            
            # 添加到过滤后的数据中
            filtered_data.append(item)
        
        # 保存修复后的文件
        with open(output_path, 'w', encoding='utf-8') as out_file:
            json.dump(filtered_data, out_file, ensure_ascii=False, indent=2)
        
        # 打印统计信息
        print(f"处理完成!")
        print(f"原始对话总数: {total_conversations}")
        print(f"删除缺少num_tokens的整个对话数: {total_no_num_tokens_removed}")
        print(f"删除包含bing/bard/chatgpt的整个对话数: {total_bing_bard_removed}")
        print(f"保留的对话数: {len(filtered_data)}")
        print(f"删除的空对话条目总数: {total_empty_removed}")
        print(f"删除的system对话条目总数: {total_system_removed}")
        print(f"修复的连续相同发言者问题总数: {total_fixed}")
        print(f"删除空对话的会话数: {len(empty_removed_items)}")
        print(f"删除system对话的会话数: {len(system_removed_items)}")
        print(f"修复连续发言者的会话数: {len(fixed_items)}")
        
        # 打印删除的整个对话ID
        if no_num_tokens_removed_items:
            print("\n删除缺少num_tokens的对话ID:")
            for i, item_id in enumerate(no_num_tokens_removed_items[:20]):
                print(f"  - {item_id}")
            if len(no_num_tokens_removed_items) > 20:
                print(f"  ... 以及其他 {len(no_num_tokens_removed_items) - 20} 个对话")
        
        if bing_bard_removed_items:
            print("\n删除包含bing/bard/chatgpt的对话ID:")
            for i, item_id in enumerate(bing_bard_removed_items[:20]):
                print(f"  - {item_id}")
            if len(bing_bard_removed_items) > 20:
                print(f"  ... 以及其他 {len(bing_bard_removed_items) - 20} 个对话")
        
        # 打印删除空对话的对话ID
        if empty_removed_items:
            print("\n删除空对话的部分会话ID及删除数量:")
            for i, (item_id, count) in enumerate(sorted(empty_removed_items.items(), key=lambda x: x[1], reverse=True)[:10]):
                print(f"  - ID: {item_id}, 删除空对话数: {count}")
            if len(empty_removed_items) > 10:
                print(f"  ... 以及其他 {len(empty_removed_items) - 10} 个会话")
        
        # 打印删除system对话的对话ID
        if system_removed_items:
            print("\n删除system对话的部分会话ID及删除数量:")
            for i, (item_id, count) in enumerate(sorted(system_removed_items.items(), key=lambda x: x[1], reverse=True)[:10]):
                print(f"  - ID: {item_id}, 删除system对话数: {count}")
            if len(system_removed_items) > 10:
                print(f"  ... 以及其他 {len(system_removed_items) - 10} 个会话")
        

        
        # 打印修复连续发言者的对话ID
        if fixed_items:
            print("\n修复连续发言者的部分会话ID及修复数量:")
            for i, (item_id, count) in enumerate(sorted(fixed_items.items(), key=lambda x: x[1], reverse=True)[:10]):
                print(f"  - ID: {item_id}, 修复连续发言者数: {count}")
            if len(fixed_items) > 10:
                print(f"  ... 以及其他 {len(fixed_items) - 10} 个会话")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        return False

def find_problematic_conversations(file_path):
    """查找并显示有问题的对话"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.loads(file.read())
        
        problematic_items = []
        
        for item in data:
            if "conversations" not in item:
                continue
            
            item_id = item.get("id", "unknown")
            conversations = item["conversations"]
            
            # 检查各种问题
            has_empty = False
            has_consecutive = False
            has_system = False
            has_bing_bard = False
            has_missing_num_tokens = False
            empty_positions = []
            consecutive_positions = []
            system_positions = []
            bing_bard_positions = []
            missing_num_tokens_positions = []
            
            prev_speaker = None
            for i, conv in enumerate(conversations):
                # 检查空对话
                value = conv.get("value", "").strip()
                if value == "":
                    has_empty = True
                    empty_positions.append(i)
                
                # 检查system发言者
                speaker = conv.get("from", "")
                if speaker == "system":
                    has_system = True
                    system_positions.append(i)
                
                # 检查bing/bard发言者
                if speaker in ["bing", "bard", "chatgpt"]:
                    has_bing_bard = True
                    bing_bard_positions.append(i)
                
                # 检查gpt对话缺少num_tokens
                if speaker == "gpt" and "num_tokens" not in conv:
                    has_missing_num_tokens = True
                    missing_num_tokens_positions.append(i)
                
                # 检查连续相同发言者
                if prev_speaker == speaker and (speaker == "human" or speaker == "gpt"):
                    has_consecutive = True
                    consecutive_positions.append(i)
                prev_speaker = speaker
            
            if has_empty or has_consecutive or has_system or has_bing_bard or has_missing_num_tokens:
                problematic_items.append({
                    "id": item_id,
                    "empty_positions": empty_positions,
                    "consecutive_positions": consecutive_positions,
                    "system_positions": system_positions,
                    "bing_bard_positions": bing_bard_positions,
                    "missing_num_tokens_positions": missing_num_tokens_positions,
                    "conversations": conversations
                })
        
        # 打印有问题的对话
        if problematic_items:
            print(f"找到 {len(problematic_items)} 个有问题的对话:")
            for i, item in enumerate(problematic_items[:5]):
                print(f"\n问题对话 {i+1}/{len(problematic_items)}, ID: {item['id']}")
                
                if item['missing_num_tokens_positions']:
                    print(f"缺少num_tokens的gpt对话位置: {item['missing_num_tokens_positions']} (将删除整个对话)")
                
                if item['empty_positions']:
                    print(f"空对话位置: {item['empty_positions']}")
                
                if item['system_positions']:
                    print(f"system发言者位置: {item['system_positions']}")
                
                if item['bing_bard_positions']:
                    print(f"bing/bard发言者位置: {item['bing_bard_positions']}")
                
                if item['consecutive_positions']:
                    print(f"连续相同发言者位置: {item['consecutive_positions']}")
                
                # 打印有问题的部分
                all_problem_positions = set(
                    item['empty_positions'] + 
                    item['system_positions'] + 
                    item['bing_bard_positions'] + 
                    item['consecutive_positions'] +
                    item['missing_num_tokens_positions']
                )
                for pos in sorted(all_problem_positions)[:3]:  # 只显示前3个问题
                    print(f"\n位置 {pos} (问题位置):")
                    conv = item['conversations'][pos]
                    print(f"  from: {conv.get('from')}")
                    print(f"  has num_tokens: {'num_tokens' in conv}")
                    print(f"  value: '{conv.get('value')[:50]}{'...' if len(conv.get('value', '')) > 50 else ''}'")
                
                print("-" * 50)
            
            if len(problematic_items) > 5:
                print(f"... 以及其他 {len(problematic_items) - 5} 个有问题的对话")
        else:
            print("未找到有问题的对话。")
        
        return problematic_items
    
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        return []

def validate_fixed_file(file_path):
    """验证修复后的文件是否还有问题"""
    print(f"\n正在验证修复后的文件: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.loads(file.read())
        
        total_issues = 0
        issue_types = {
            'empty': 0,
            'system': 0,
            'bing_bard': 0,
            'consecutive': 0,
            'missing_num_tokens': 0
        }
        
        for item in data:
            if "conversations" not in item:
                continue
            
            conversations = item["conversations"]
            prev_speaker = None
            
            for i, conv in enumerate(conversations):
                # 检查空对话
                value = conv.get("value", "").strip()
                if value == "":
                    issue_types['empty'] += 1
                    total_issues += 1
                
                # 检查system发言者
                speaker = conv.get("from", "")
                if speaker == "system":
                    issue_types['system'] += 1
                    total_issues += 1
                
                # 检查bing/bard发言者
                if speaker in ["bing", "bard", "chatgpt"]:
                    issue_types['bing_bard'] += 1
                    total_issues += 1
                
                # 检查gpt对话缺少num_tokens
                if speaker == "gpt" and "num_tokens" not in conv:
                    issue_types['missing_num_tokens'] += 1
                    total_issues += 1
                
                # 检查连续相同发言者
                if prev_speaker == speaker and (speaker == "human" or speaker == "gpt"):
                    issue_types['consecutive'] += 1
                    total_issues += 1
                
                prev_speaker = speaker
        
        if total_issues == 0:
            print("✅ 验证通过！文件中没有发现问题。")
        else:
            print(f"❌ 验证失败！仍有 {total_issues} 个问题:")
            for issue_type, count in issue_types.items():
                if count > 0:
                    print(f"  - {issue_type}: {count} 个")
        
        return total_issues == 0
        
    except json.JSONDecodeError as e:
        print(f"❌ 验证失败！JSON 解析错误: {e}")
        return False

if __name__ == "__main__":
    file_path = "ShareGPT.json"
    output_path = "ShareGPT_fixed4.json"
    
    # 首先查找有问题的对话
    print("正在查找有问题的对话...")
    problematic_items = find_problematic_conversations(file_path)
    
    if problematic_items:
        print(f"\n是否要修复这些问题? (y/n)")
        choice = input().strip().lower()
        
        if choice == 'y':
            # 修复问题
            print("\n正在修复问题...")
            success = fix_consecutive_speakers_and_empty(file_path, output_path)
            
            if success:
                # 验证修复后的文件
                validate_fixed_file(output_path)
        else:
            print("已取消修复。")
    else:
        print("无需修复。")