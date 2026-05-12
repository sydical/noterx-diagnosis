#!/usr/bin/env python3
"""
NoteRx - 小红书笔记诊断脚本
基于 874 条真实笔记 + 2465 条评论的数据驱动分析
"""

import json
import re
from typing import Dict, List, Tuple, Optional

# 品类权重（基于回归分析）
CATEGORY_WEIGHTS = {
    "美食": {"标题": 0.713, "内容": 0.130, "视觉": 0.110, "标签": 0.030, "互动": 0.017},
    "穿搭": {"视觉": 0.250, "标题": 0.395, "互动": 0.170, "内容": 0.120, "标签": 0.115},
    "旅游": {"标签": 0.520, "视觉": 0.250, "内容": 0.120, "标题": 0.080, "互动": 0.030},
    "科技": {"图片": 0.410, "内容": 0.350, "标题": 0.150, "标签": 0.060, "互动": 0.030},
    "生活": {"标题": 1.000, "标签": 0.400, "内容": 0.250, "视觉": 0.200, "互动": 0.150},
}

# 品类特征词
CATEGORY_KEYWORDS = {
    "美食": ["好吃", "美食", "做法", "食谱", "做饭", "炒菜", "餐厅", "探店", "吃", "烹饪", "菜谱", "配方", "味道", "口感"],
    "穿搭": ["穿搭", "衣服", "搭配", "裙子", "裤子", "上衣", "这件", "试穿", "look", "OOTD", "时尚", "显瘦", "气质"],
    "旅游": ["旅游", "旅行", "打卡", "景点", "酒店", "海边", "城市", "周末", "攻略", "拍照", "风景", "度假", "出行"],
    "科技": ["科技", "数码", "手机", "电脑", "app", "软件", "测评", "评测", "工具", "教程", "技巧", "AI", "智能"],
    "生活": ["生活", "日常", "分享", "感悟", "成长", "职场", "赚钱", "省钱", "经验", "心得", "故事", "人生", "健康", "感情"],
}

# 黄金发布时段
BEST_POST_TIME = "17:00-19:00"

# 钩子最优数量
OPTIMAL_HOOKS = 3
HOOKS_COLLAPSE = 4


def detect_category(text: str) -> str:
    """根据内容判断品类"""
    text_lower = text.lower()
    scores = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        scores[category] = score
    
    if max(scores.values()) == 0:
        return "生活"  # 默认生活类
    return max(scores, key=scores.get)


def extract_hooks(title: str) -> List[str]:
    """提取标题中的钩子"""
    hooks = []
    
    # 数字钩子
    numbers = re.findall(r'\d+[万个百千万亿]', title)
    hooks.extend([f"数字:{n}" for n in numbers])
    
    # 情感钩子
    emotion_words = ['绝了', '惊艳', 'yyds', '太好吃了', '美到', '牛', '爆', '好用到', '吹爆', '逆袭', '哭', '笑死', '救命', '太香了', '后劲']
    for word in emotion_words:
        if word in title:
            hooks.append(f"情感:{word}")
    
    # 悬念钩子
    suspense_words = ['千万别', '竟然', '99%', '不知道', '除非', '不敢信', '以为', '其实', '真相', '曝光']
    for word in suspense_words:
        if word in title:
            hooks.append(f"悬念:{word}")
    
    return hooks[:5]  # 最多5个


def check_title_structure(title: str) -> Dict:
    """分析标题结构"""
    length = len(title)
    
    # 检查数字
    has_number = bool(re.search(r'\d', title))
    
    # 检查情感词
    emotion_list = ['绝了', '惊艳', 'yyds', '太好吃了', '美到', '牛', '爆', '好用到', '吹爆', '逆袭', '救命', '太香了', '后劲', '太绝了', '被问', '求链接']
    has_emotion = any(word in title for word in emotion_list)
    
    # 检查悬念
    suspense_list = ['千万别', '竟然', '99%', '不知道', '除非', '不敢信', '以为', '其实', '真相', '曝光', '别点']
    has_suspense = any(word in title for word in suspense_list)
    
    return {
        "长度": length,
        "has_number": has_number,
        "has_emotion": has_emotion,
        "has_suspense": has_suspense,
        "结构分数": sum([has_number, has_emotion, has_suspense]),
        "is_optimal": has_number and has_emotion and has_suspense,
    }


def predict_comments(category: str, content: str = "") -> Dict:
    """预测评论区画像"""
    personas = {
        "美食": {"种草型": 0.254, "经验型": 0.369, "调侃型": 0.303, "质疑型": 0.170, "求购型": 0.079, "路人型": 0.311},
        "穿搭": {"种草型": 0.280, "求购型": 0.150, "经验型": 0.200, "质疑型": 0.120, "调侃型": 0.180, "路人型": 0.250},
        "旅游": {"种草型": 0.300, "求购型": 0.150, "经验型": 0.250, "质疑型": 0.150, "调侃型": 0.150, "路人型": 0.250},
        "科技": {"质疑型": 0.272, "经验型": 0.300, "种草型": 0.200, "调侃型": 0.150, "路人型": 0.200, "求购型": 0.100},
        "生活": {"经验型": 0.300, "调侃型": 0.250, "种草型": 0.200, "质疑型": 0.150, "路人型": 0.200, "求购型": 0.080},
    }
    return personas.get(category, personas["生活"])


def generate_rewrite(title: str, category: str) -> List[str]:
    """生成改写方案"""
    rewrites = []
    
    if category == "美食":
        rewrites.append(f"5分钟搞定！这道菜我妈做了20年")
        rewrites.append(f"被这家店惊艳到了！！{title[:10] if len(title) > 10 else title}")
    elif category == "穿搭":
        rewrites.append(f"这套绝了！被问链接问麻了")
        rewrites.append(f"小个子显高神器！{title[:10] if len(title) > 10 else title}")
    elif category == "旅游":
        rewrites.append(f"这个海边美到犯规！99%的人不知道")
        rewrites.append(f"{title[:5] if len(title) > 5 else title}后劲太大，去了就不想回来")
    elif category == "科技":
        rewrites.append(f"救命！这个工具太牛了，后悔没早知道")
        rewrites.append(f"竟然才发现！{title[:10] if len(title) > 10 else title}")
    else:
        rewrites.append(f"从月薪3千到3万，我终于明白了：{title[:10] if len(title) > 10 else title}")
        rewrites.append(f"真心建议：别错过这篇！{title}")
    
    return rewrites[:3]


def diagnose(title: str, content: str = "", category_hint: str = "") -> Dict:
    """综合诊断"""
    
    # 1. 判断品类
    full_text = f"{title} {content}"
    category = category_hint if category_hint else detect_category(full_text)
    
    # 2. 分析标题结构
    title_analysis = check_title_structure(title)
    
    # 3. 提取钩子
    hooks = extract_hooks(title)
    
    # 4. 预测评论
    comment_personas = predict_comments(category, full_text)
    
    # 5. 生成改写
    rewrites = generate_rewrite(title, category)
    
    # 6. 计算综合评分（简化版）
    score = 60 + title_analysis["结构分数"] * 10 + (25 if len(hooks) == OPTIMAL_HOOKS else 0)
    
    return {
        "category": category,
        "title_analysis": title_analysis,
        "hooks": hooks,
        "hook_count": len(hooks),
        "comment_personas": comment_personas,
        "rewrites": rewrites,
        "estimated_score": min(score, 95),
        "best_post_time": BEST_POST_TIME,
        "tips": get_tips(category, title_analysis, hooks),
    }


def get_tips(category: str, title_analysis: Dict, hooks: List) -> List[str]:
    """获取优化建议"""
    tips = []
    
    # 标题建议
    if not title_analysis["has_number"]:
        tips.append("添加数字（如：3个方法、5分钟、99%）")
    if not title_analysis["has_emotion"]:
        tips.append("添加情感词（如：绝了、惊艳、yyds）")
    if not title_analysis["has_suspense"]:
        tips.append("添加悬念（如：千万别、竟然、99%不知道）")
    
    # 钩子建议
    if len(hooks) == 0:
        tips.append("标题缺乏吸引力，考虑加入爆款元素")
    elif len(hooks) >= HOOKS_COLLAPSE:
        tips.append(f"钩子过多（{len(hooks)}个），建议精简到3个以内")
    
    # 品类专属建议
    if category == "美食":
        tips.extend(["内容加入口感描述（好吃到哭、被惊艳到）", "中等长度100-300字最优"])
    elif category == "穿搭":
        tips.extend(["封面图质量是关键，文字只能解释1.7%", "评论区求链接，多引导互动"])
    elif category == "旅游":
        tips.extend(["标签策略很重要（52%权重）", "简单地名+情感表达更有效"])
    elif category == "科技":
        tips.extend(["多用表情符号和感叹句", "内容要有信息增量，硬核一点"])
    elif category == "生活":
        tips.extend(["个人觉醒/改变故事最能打", "引导评论互动，提升评论区活跃度"])
    
    # 发布时间
    tips.append(f"黄金发布时段：17:00-19:00（比凌晨3点高5658倍！）")
    
    return tips


def print_diagnosis(result: Dict):
    """打印诊断结果"""
    print("\n" + "="*50)
    print(f"📊 品类诊断：{result['category']}")
    print("="*50)
    print(f"📝 标题结构分析：")
    ta = result['title_analysis']
    print(f"   - 长度：{ta['长度']}字")
    print(f"   - 数字：{'✅' if ta['has_number'] else '❌'}")
    print(f"   - 情感：{'✅' if ta['has_emotion'] else '❌'}")
    print(f"   - 悬念：{'✅' if ta['has_suspense'] else '❌'}")
    print(f"   - 结构分数：{ta['结构分数']}/3")
    
    print(f"\n🎣 钩子检测（{result['hook_count']}个）：")
    if result['hooks']:
        for hook in result['hooks']:
            print(f"   - {hook}")
    else:
        print("   - 无明显钩子")
    
    print(f"\n💬 评论区预测：")
    for persona, ratio in sorted(result['comment_personas'].items(), key=lambda x: -x[1]):
        bar = "█" * int(ratio * 20)
        print(f"   {persona}: {bar} ({ratio*100:.1f}%)")
    
    print(f"\n✨ 预估评分：{result['estimated_score']}/100")
    
    print(f"\n📋 优化建议：")
    for tip in result['tips']:
        print(f"   • {tip}")
    
    print(f"\n🔄 改写方案：")
    for i, rewrite in enumerate(result['rewrites'], 1):
        print(f"   {i}. {rewrite}")
    
    print(f"\n⏰ 黄金发布：{result['best_post_time']}")
    print("="*50)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        title = sys.argv[1]
        content = sys.argv[2] if len(sys.argv) > 2 else ""
        category = sys.argv[3] if len(sys.argv) > 3 else ""
        
        result = diagnose(title, content, category)
        print_diagnosis(result)
    else:
        # Demo
        print("NoteRx - 小红书笔记诊断工具")
        print("用法: python3 diagnose.py <标题> [内容] [品类]")
        print()
        
        demo_titles = [
            "分享一个好用的护肤方法",
            "5分钟搞定！这道菜我妈做了20年",
            "这套穿搭绝了！被问链接问麻了",
        ]
        
        for title in demo_titles:
            result = diagnose(title)
            print_diagnosis(result)
            print()