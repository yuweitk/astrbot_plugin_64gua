import os
import random
import datetime
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
        self.user_quota = {}  # 用户ID: [剩余次数, 最后使用日期]
        
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

    def _update_quota(self, user_id: str):
        """更新用户配额系统"""
        today = datetime.date.today()
        
        # 跨天重置次数
        if user_id in self.user_quota:
            last_date = self.user_quota[user_id][1]
            if last_date != today:
                self.user_quota[user_id] = [3, today]
        else:
            self.user_quota[user_id] = [3, today]
            
        # 扣除次数并返回剩余值
        self.user_quota[user_id][0] -= 1
        return self.user_quota[user_id][0]

    @filter.command("金钱卦")
    async def send_random_gua(self, event: AstrMessageEvent):
        if not self.gua_images:
            yield event.plain_result("未找到卦象图片，请联系管理员检查插件配置")
            return

        try:
            user_id = event.get_sender_id()
            user_name = event.get_sender_name()  # 根据SDK实际情况调整
            
            # 配额检查
            if user_id in self.user_quota:
                remaining = self.user_quota[user_id][0]
                if remaining <= 0:
                    yield event.chain_result([
                        Comp.At(user_id),
                        Comp.Plain("今日卦象已卜满三次，请明日再来（子时刷新）")
                    ])
                    return
            
            # 更新配额系统
            remaining = self._update_quota(user_id)
            
            # 构建消息链
            selected_image = random.choice(self.gua_images)
            image_path = os.path.join(IMAGE_DIR, selected_image)
            
            chain = [
                Comp.At(user_id),
                Comp.Plain(f"\n🔮 周易金钱卦第{3 - remaining +1}次推算："),
                Comp.Image.fromFileSystem(image_path),
                Comp.Plain(f"\n『卦象已显，剩余次数：{remaining}』")
            ]
            
            yield event.chain_result(chain)
            logger.info(f"用户 {user_id} 获取卦象 {selected_image}")

        except FileNotFoundError:
            error_msg = f"卦象图片 {selected_image} 不存在"
            logger.error(error_msg)
            yield event.chain_result([
                Comp.At(user_id),
                Comp.Plain("卦象显化失败，请稍后再试")
            ])
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            yield event.chain_result([
                Comp.At(user_id),
                Comp.Plain("卦象推算异常，请联系管理员")
            ])

    async def terminate(self):
        self.gua_images.clear()
        self.user_quota.clear()
        logger.info("周易金钱卦插件已卸载")
