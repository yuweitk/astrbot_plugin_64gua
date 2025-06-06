import os
import random
from datetime import datetime
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp

PLUGIN_DIR = os.path.dirname(__file__)
IMAGE_DIR = os.path.join(PLUGIN_DIR, "64gua")

@register("astrbot_plugin_64gua", "IamAGod", "周易金钱卦插件", "1.0.0")
class GuaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.gua_images = []
        self.total_gua = 64
        self.user_quota = {}  # 用户占卜记录

    async def initialize(self):
        try:
            if not os.path.exists(IMAGE_DIR):
                logger.error(f"卦象文件夹 {IMAGE_DIR} 不存在")
                return
            
            self.gua_images = [
                f for f in os.listdir(IMAGE_DIR)
                if f.endswith('.jpg') and f.startswith('64gua_')
            ]
            
            if len(self.gua_images) != self.total_gua:
                logger.warning(f"卦象图片数量异常，期望64张，实际找到{len(self.gua_images)}张")
            
            logger.info(f"成功加载 {len(self.gua_images)} 张卦象图片")

        except Exception as e:
            logger.error(f"初始化失败: {str(e)}")
            self.gua_images = []

    @filter.command("金钱卦")
    async def send_random_gua(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        current_date = datetime.now().date()

        # 初始化次数
        if user_id not in self.user_quota or self.user_quota[user_id]['date'] != current_date:
            self.user_quota[user_id] = {'date': current_date, 'count': 3}
        
        remaining = self.user_quota[user_id]['count']
        if remaining <= 0:
            yield event.plain_result("今日占卜次数已用尽，请明日再来")
            return

        self.user_quota[user_id]['count'] -= 1
        remaining_after = self.user_quota[user_id]['count']

        if not self.gua_images:
            yield event.plain_result("未找到卦象图片，请联系管理员检查插件配置")
            return

        try:
            selected_image = random.choice(self.gua_images)
            image_path = os.path.join(IMAGE_DIR, selected_image)
            
            # 构建提示语
            chain = [
                Comp.Plain("🔮 周易金钱卦推算结果："),
                Comp.Image.fromFileSystem(image_path),
                Comp.Plain(f"\n『卦象已显，吉凶自辨』\n✨ 剩余占卜次数：{remaining_after}次")
            ]
            
            yield event.chain_result(chain)
            logger.info(f"用户 {user_id} 获取卦象 {selected_image}")

        except FileNotFoundError:
            logger.error(f"卦象图片 {selected_image} 不存在")
            yield event.plain_result("卦象显化失败，请稍后再试")
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            yield event.plain_result("卦象推算异常，请联系管理员")

    async def terminate(self):
        self.gua_images.clear()
        self.user_quota.clear()
        logger.info("周易金钱卦插件已卸载")
