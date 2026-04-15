import os
import sys
# 将项目根目录添加到路径，确保可以导入 app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.rag_service import rag_service

TRAVEL_KNOWLEDGE = [
    # 摄影器材知识
    "DJI Pocket 3 拍摄设置：在白天大光比环境下，推荐使用 ND 滤镜。开启 D-Log M 模式以保留更多高光细节。构图时使用三轴云台的‘跟随后排’模式，适合拍摄行走中的第一视角路径。",
    "相机夜景人像参数：光圈 f/1.8 - f/2.8，快门 1/60s 以上防止抖动，ISO 根据环境光线在 800-3200 之间。构图建议利用背景霓虹灯形成虚化光斑。",
    "旅行人像构图：三分法构图是将主体放在画面的 1/3 处；利用道路、护栏形成的‘引导线’增加画面纵深感。",
    
    # 旅游路线与攻略（以热门地北京为例，可扩展）
    "北京故宫深度旅游路线：建议从午门进入，沿中轴线观赏，重点关注东六宫的珍宝馆。下午三点后的侧影光最适合拍摄红墙。",
    "北京胡同美食推荐：后海附近的胡同里隐藏着许多地道卤煮。拍摄美食时，建议倾斜 45 度角，微距对焦，展现食物细节。",
]

def seed_database():
    print("正在初始化向量数据库并注入旅游/摄影知识...")
    try:
        rag_service.add_documents(TRAVEL_KNOWLEDGE)
        print("数据库初始化成功！")
    except Exception as e:
        print(f"初始化失败: {e}")

if __name__ == "__main__":
    seed_database()
