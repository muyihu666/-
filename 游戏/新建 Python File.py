import pygame
import sys
import random
import os

# 初始化pygame
pygame.init()

# 屏幕设置
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("外汇交易模拟器")

# 颜色定义
BACKGROUND = (10, 20, 35)
PANEL_BG = (25, 40, 65)
TEXT_COLOR = (220, 230, 255)
HIGHLIGHT = (0, 200, 255)
PROFIT_COLOR = (0, 230, 150)
LOSS_COLOR = (255, 80, 80)
BUTTON_COLOR = (40, 120, 180)
BUTTON_HOVER = (60, 160, 230)
GRAPH_COLORS = [
    (0, 180, 255),  # USD
    (255, 150, 50),  # EUR
    (0, 230, 150),  # GBP
    (180, 100, 255),  # JPY
    (255, 100, 150),  # AUD
    (100, 230, 255)  # CAD
]


# 中文字体支持
def load_font(size):
    """尝试加载中文字体，如果失败则使用默认字体"""
    try:
        # 尝试加载系统字体（Windows通常是SimHei）
        return pygame.font.SysFont('SimHei', size)
    except:
        try:
            # 尝试加载其他常见中文字体
            return pygame.font.SysFont('Microsoft YaHei', size)
        except:
            try:
                # 尝试加载Arial Unicode MS（如果可用）
                return pygame.font.SysFont('Arial Unicode MS', size)
            except:
                # 使用pygame的默认字体
                return pygame.font.Font(None, size)


# 创建不同大小的字体
font_small = load_font(18)
font_medium = load_font(24)
font_large = load_font(32)
font_title = load_font(40)


# 货币类
class Currency:
    def __init__(self, code, name, initial_rate, volatility):
        self.code = code
        self.name = name
        self.rate = initial_rate  # 相对于基础货币（USD）的汇率
        self.volatility = volatility
        self.history = [initial_rate]
        self.color = GRAPH_COLORS[len(self.history) % len(GRAPH_COLORS)]

    def update_rate(self):
        # 随机波动，但有一定趋势性
        change = random.uniform(-self.volatility, self.volatility)

        # 增加趋势性：如果最近趋势向上，更可能继续向上，反之亦然
        if len(self.history) > 5:
            last_trend = self.history[-1] - self.history[-6]
            if last_trend > 0:
                change = abs(change) * 0.7
            else:
                change = -abs(change) * 0.7

        self.rate = max(0.1, self.rate * (1 + change))
        self.history.append(self.rate)
        if len(self.history) > 100:
            self.history.pop(0)


# 玩家类
class Player:
    def __init__(self):
        self.cash = 10000.0  # 初始资金（USD）
        self.portfolio = {}  # 持有的货币 {currency_code: amount}
        self.total_value = self.cash
        self.profit = 0.0
        self.transactions = []

    def buy_currency(self, currency, amount, rate):
        cost = amount * rate
        if cost > self.cash:
            return False, "资金不足"

        self.cash -= cost
        if currency.code in self.portfolio:
            self.portfolio[currency.code] += amount
        else:
            self.portfolio[currency.code] = amount

        self.transactions.append(f"买入 {amount:.2f} {currency.code} @ {rate:.4f}")
        return True, f"成功买入 {amount:.2f} {currency.code}"

    def sell_currency(self, currency, amount, rate):
        if currency.code not in self.portfolio or self.portfolio[currency.code] < amount:
            return False, "持有量不足"

        self.cash += amount * rate
        self.portfolio[currency.code] -= amount

        if self.portfolio[currency.code] < 0.01:  # 清理接近0的持仓
            del self.portfolio[currency.code]

        self.transactions.append(f"卖出 {amount:.2f} {currency.code} @ {rate:.4f}")
        return True, f"成功卖出 {amount:.2f} {currency.code}"

    def update_portfolio_value(self, currencies):
        self.total_value = self.cash
        for code, amount in self.portfolio.items():
            currency = next((c for c in currencies if c.code == code), None)
            if currency:
                self.total_value += amount * currency.rate
        self.profit = self.total_value - 10000.0


# 按钮类
class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False

    def draw(self, surface):
        color = BUTTON_HOVER if self.hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, HIGHLIGHT, self.rect, 2, border_radius=8)

        text_surf = font_medium.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.action:
                return self.action()
        return None


# 创建货币
currencies = [
    Currency("USD", "美元", 1.0, 0.005),
    Currency("EUR", "欧元", 1.08, 0.008),
    Currency("GBP", "英镑", 1.27, 0.01),
    Currency("JPY", "日元", 0.0091, 0.015),
    Currency("AUD", "澳元", 0.66, 0.012),
    Currency("CAD", "加元", 0.74, 0.009)
]

# 创建玩家
player = Player()


# 创建按钮
def buy_action():
    return "buy"


def sell_action():
    return "sell"


def next_day_action():
    return "next_day"


buttons = [
    Button(WIDTH - 220, HEIGHT - 80, 100, 40, "买入", buy_action),
    Button(WIDTH - 110, HEIGHT - 80, 100, 40, "卖出", sell_action),
    Button(WIDTH - 220, HEIGHT - 140, 210, 40, "下一天", next_day_action)
]


# ...（前面的代码保持不变）...

# 交易面板类
class TradePanel:
    def __init__(self):
        self.active = False
        self.mode = ""  # "buy" or "sell"
        self.selected_currency = None
        self.amount_str = "100.0"  # 使用字符串存储输入
        self.message = ""
        self.message_timer = 0
        self.input_active = True  # 默认激活输入框
        self.cursor_visible = True
        self.cursor_timer = 0

    def open(self, mode, currency=None):
        self.active = True
        self.mode = mode
        self.selected_currency = currency
        self.amount_str = "100.0"
        self.message = ""
        self.input_active = True
        self.cursor_visible = True
        self.cursor_timer = 0

    def close(self):
        self.active = False

    def draw(self, surface):
        if not self.active:
            return

        # 绘制半透明背景
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        surface.blit(s, (0, 0))

        # 绘制面板
        panel_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 150, 400, 300)
        pygame.draw.rect(surface, PANEL_BG, panel_rect, border_radius=12)
        pygame.draw.rect(surface, HIGHLIGHT, panel_rect, 2, border_radius=12)

        # 标题
        title = "买入货币" if self.mode == "buy" else "卖出货币"
        title_surf = font_large.render(title, True, HIGHLIGHT)
        surface.blit(title_surf, (panel_rect.centerx - title_surf.get_width() // 2, panel_rect.y + 20))

        # 货币信息
        if self.selected_currency:
            currency_text = f"{self.selected_currency.name} ({self.selected_currency.code})"
            rate_text = f"汇率: 1 {self.selected_currency.code} = ${self.selected_currency.rate:.4f}"
            pygame.draw.rect(surface, (40, 60, 100),
                             (panel_rect.x + 20, panel_rect.y + 70, panel_rect.width - 40, 40),
                             border_radius=6)

            curr_surf = font_medium.render(currency_text, True, TEXT_COLOR)
            rate_surf = font_small.render(rate_text, True, TEXT_COLOR)
            surface.blit(curr_surf, (panel_rect.x + 30, panel_rect.y + 75))
            surface.blit(rate_surf, (panel_rect.x + 30, panel_rect.y + 95))

        # 金额输入
        amount_text = font_medium.render("交易金额:", True, TEXT_COLOR)
        surface.blit(amount_text, (panel_rect.x + 30, panel_rect.y + 130))

        # 输入框
        input_rect = pygame.Rect(panel_rect.x + 150, panel_rect.y + 125, 150, 30)
        input_color = HIGHLIGHT if self.input_active else (100, 130, 160)
        pygame.draw.rect(surface, (40, 60, 100), input_rect, border_radius=4)
        pygame.draw.rect(surface, input_color, input_rect, 2, border_radius=4)

        # 绘制输入文本和光标
        amount_surf = font_medium.render(self.amount_str, True, TEXT_COLOR)
        surface.blit(amount_surf, (input_rect.x + 5, input_rect.y + 3))

        # 绘制闪烁的光标
        if self.input_active and self.cursor_visible:
            text_width = amount_surf.get_width()
            cursor_pos = (input_rect.x + 5 + text_width, input_rect.y + 5)
            pygame.draw.line(surface, TEXT_COLOR, cursor_pos, (cursor_pos[0], cursor_pos[1] + 20), 2)

        # 按钮
        confirm_btn = Button(panel_rect.x + 80, panel_rect.y + 220, 100, 40, "确认")
        cancel_btn = Button(panel_rect.x + 220, panel_rect.y + 220, 100, 40, "取消")

        mouse_pos = pygame.mouse.get_pos()
        confirm_btn.check_hover(mouse_pos)
        cancel_btn.check_hover(mouse_pos)

        confirm_btn.draw(surface)
        cancel_btn.draw(surface)

        # 显示消息
        if self.message:
            msg_color = PROFIT_COLOR if "成功" in self.message else LOSS_COLOR
            msg_surf = font_medium.render(self.message, True, msg_color)
            surface.blit(msg_surf, (panel_rect.centerx - msg_surf.get_width() // 2, panel_rect.y + 180))

        # 提示文本
        hint_text = font_small.render("输入金额后按回车确认交易", True, (180, 200, 230))
        surface.blit(hint_text, (panel_rect.centerx - hint_text.get_width() // 2, panel_rect.y + 160))

        return confirm_btn, cancel_btn, input_rect

    def update(self):
        """更新光标闪烁状态"""
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # 每半秒切换一次
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def handle_input(self, event):
        # 光标闪烁逻辑
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # 每半秒切换一次
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

        if event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_BACKSPACE:
                self.amount_str = self.amount_str[:-1]
                if not self.amount_str:
                    self.amount_str = "0"
            elif event.key == pygame.K_RETURN:
                return "confirm"
            elif event.key == pygame.K_ESCAPE:
                return "cancel"
            elif event.key == pygame.K_TAB:
                self.input_active = True  # Tab键保持输入激活
            elif event.unicode.isdigit() or event.unicode == '.':
                # 防止输入多个小数点
                if event.unicode == '.' and '.' in self.amount_str:
                    return None

                # 添加字符
                if self.amount_str == "0" and event.unicode != '.':
                    self.amount_str = event.unicode
                else:
                    self.amount_str += event.unicode

                # 限制最大长度
                if len(self.amount_str) > 10:
                    self.amount_str = self.amount_str[:10]
        return None


# ...（后面的代码保持不变）...


# 创建交易面板
trade_panel = TradePanel()


# 绘制折线图
def draw_line_chart(surface, x, y, width, height, data, colors, labels=None):
    if not data or not data[0]:
        return

    # 找到最大值和最小值
    all_values = [val for sublist in data for val in sublist]
    max_value = max(all_values)
    min_value = min(all_values)
    range_val = max_value - min_value
    if range_val == 0:
        range_val = 1

    # 绘制背景
    pygame.draw.rect(surface, (20, 35, 60), (x, y, width, height), border_radius=8)
    pygame.draw.rect(surface, HIGHLIGHT, (x, y, width, height), 1, border_radius=8)

    # 绘制坐标轴
    pygame.draw.line(surface, TEXT_COLOR, (x + 40, y + height - 30), (x + width - 10, y + height - 30), 2)
    pygame.draw.line(surface, TEXT_COLOR, (x + 40, y + 10), (x + 40, y + height - 30), 2)

    # 绘制数据
    point_radius = 3
    for idx, values in enumerate(data):
        if len(values) < 2:
            continue

        color = colors[idx % len(colors)]
        points = []
        for i, val in enumerate(values):
            x_pos = x + 40 + (i / (len(values) - 1)) * (width - 50)
            y_pos = y + height - 30 - ((val - min_value) / range_val * (height - 40))
            points.append((x_pos, y_pos))

        # 绘制连线
        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points, 2)

        # 绘制点
        for point in points:
            pygame.draw.circle(surface, color, point, point_radius)

    # 绘制图例
    if labels:
        legend_y = y + 10
        for i, label in enumerate(labels):
            pygame.draw.line(surface, colors[i], (x + width - 180, legend_y + 10), (x + width - 150, legend_y + 10), 2)
            label_surf = font_small.render(label, True, TEXT_COLOR)
            surface.blit(label_surf, (x + width - 140, legend_y))


# 显示开始界面
def show_start_screen():
    screen.fill(BACKGROUND)

    # 标题
    title = font_title.render("外汇交易模拟器", True, HIGHLIGHT)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))

    # 游戏介绍
    intro_lines = [
        "欢迎来到外汇交易模拟器！",
        "",
        "游戏背景：",
        "您是一名初入外汇市场的交易员，",
        "拥有初始资金10,000美元。",
        "通过买卖不同货币，应对市场波动，",
        "目标是最大化您的财富！",
        "",
        "操作指南：",
        "1. 从左侧货币列表中选择一种货币",
        "2. 点击'买入'或'卖出'按钮进行交易",
        "3. 在交易面板中输入交易金额",
        "4. 点击'下一天'推进市场变化",
        "5. 观察市场动态和汇率变化",
        "6. 管理投资组合，最大化资产价值",
        "",
        "提示：",
        "- 汇率会随时间波动",
        "- 随机市场事件会影响汇率",
        "- 关注24小时变化率做出决策",
        "",
        "点击任意键开始游戏..."
    ]

    y_pos = 150
    for line in intro_lines:
        if line == "":
            y_pos += 10
            continue

        if "游戏背景" in line or "操作指南" in line or "提示" in line:
            text_surf = font_medium.render(line, True, HIGHLIGHT)
        else:
            text_surf = font_small.render(line, True, TEXT_COLOR)

        screen.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, y_pos))
        y_pos += 30 if line in ["游戏背景：", "操作指南：", "提示："] else 25

    pygame.display.flip()

    # 更健壮的等待循环
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False


# 主游戏循环
clock = pygame.time.Clock()
current_day = 1
selected_currency = None
market_events = [
    "美联储宣布加息25个基点",
    "欧洲央行维持利率不变",
    "英国通胀数据超预期",
    "日本央行干预外汇市场",
    "大宗商品价格大幅上涨",
    "地缘政治紧张局势升级",
    "全球经济衰退担忧加剧",
    "就业数据好于预期",
    "贸易赤字扩大",
    "消费者信心指数上升"
]
event_message = ""
event_timer = 0

# 显示开始界面
try:
    show_start_screen()
except KeyboardInterrupt:
    pygame.quit()
    sys.exit()

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if trade_panel.active:
            confirm_btn, cancel_btn, input_rect = trade_panel.draw(screen)
            confirm_btn.check_hover(mouse_pos)
            cancel_btn.check_hover(mouse_pos)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_rect.collidepoint(mouse_pos):
                    trade_panel.input_active = True
                    if trade_panel.amount_str == "100.0":
                        trade_panel.amount_str = ""
                else:
                    trade_panel.input_active = False

                if cancel_btn.rect.collidepoint(mouse_pos):
                    trade_panel.close()
                elif confirm_btn.rect.collidepoint(mouse_pos):
                    try:
                        amount = float(trade_panel.amount_str)
                        if trade_panel.mode == "buy":
                            success, msg = player.buy_currency(
                                trade_panel.selected_currency,
                                amount,
                                trade_panel.selected_currency.rate
                            )
                        else:
                            success, msg = player.sell_currency(
                                trade_panel.selected_currency,
                                amount,
                                trade_panel.selected_currency.rate
                            )
                        trade_panel.message = msg
                        if success:
                            trade_panel.message_timer = 180
                    except ValueError:
                        trade_panel.message = "无效金额"
                        trade_panel.message_timer = 180

            trade_panel.handle_input(event)
        else:
            # 这里是 trade_panel 不活跃的逻辑（保留原样）
            # 不要在这里访问 confirm_btn 或 cancel_btn
            for button in buttons:
                action = button.handle_event(event)
                if action == "buy" and selected_currency:
                    trade_panel.open("buy", selected_currency)
                elif action == "sell" and selected_currency:
                    trade_panel.open("sell", selected_currency)
                elif action == "next_day":
                    for currency in currencies:
                        currency.update_rate()
                    player.update_portfolio_value(currencies)
                    if random.random() < 0.3:
                        event_message = random.choice(market_events)
                        event_timer = 180
                        for currency in currencies:
                            if random.random() < 0.5:
                                change = random.uniform(-0.05, 0.05)
                                currency.rate = max(0.1, currency.rate * (1 + change))
                    current_day += 1

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, currency in enumerate(currencies):
                    currency_rect = pygame.Rect(30, 190 + i * 80, 300, 70)
                    if currency_rect.collidepoint(mouse_pos):
                        selected_currency = currency


    # 更新
    if trade_panel.active and trade_panel.message_timer > 0:
        trade_panel.message_timer -= 1
        if trade_panel.message_timer == 0:
            trade_panel.close()

    if event_timer > 0:
        event_timer -= 1

    # 绘制界面
    screen.fill(BACKGROUND)

    # 绘制标题
    title = font_title.render("外汇交易模拟器", True, HIGHLIGHT)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

    # 绘制日期和玩家信息
    day_text = font_medium.render(f"第 {current_day} 天", True, TEXT_COLOR)
    cash_text = font_medium.render(f"现金: ${player.cash:.2f}", True, TEXT_COLOR)
    value_text = font_medium.render(f"总资产: ${player.total_value:.2f}", True, TEXT_COLOR)

    profit_color = PROFIT_COLOR if player.profit >= 0 else LOSS_COLOR
    profit_text = font_medium.render(f"收益: ${player.profit:.2f} ({player.profit / 100:.2f}%)", True, profit_color)

    screen.blit(day_text, (30, 80))
    screen.blit(cash_text, (200, 80))
    screen.blit(value_text, (400, 80))
    screen.blit(profit_text, (630, 80))

    # 绘制货币列表
    pygame.draw.rect(screen, PANEL_BG, (20, 140, 320, 420), border_radius=12)
    pygame.draw.rect(screen, HIGHLIGHT, (20, 140, 320, 420), 2, border_radius=12)

    list_title = font_large.render("货币市场", True, HIGHLIGHT)
    screen.blit(list_title, (30, 150))

    for i, currency in enumerate(currencies):
        currency_rect = pygame.Rect(30, 190 + i * 80, 300, 70)

        # 高亮选中的货币
        if currency == selected_currency:
            pygame.draw.rect(screen, (40, 70, 120), currency_rect, border_radius=8)
            pygame.draw.rect(screen, HIGHLIGHT, currency_rect, 2, border_radius=8)
        else:
            pygame.draw.rect(screen, (30, 50, 90), currency_rect, border_radius=8)

        # 货币信息
        code_text = font_large.render(currency.code, True, TEXT_COLOR)
        name_text = font_small.render(currency.name, True, TEXT_COLOR)
        rate_text = font_medium.render(f"1 {currency.code} = ${currency.rate:.4f}", True, TEXT_COLOR)

        # 24小时变化
        if len(currency.history) > 1:
            change = ((currency.rate - currency.history[-2]) / currency.history[-2]) * 100
            change_color = PROFIT_COLOR if change >= 0 else LOSS_COLOR
            change_text = font_small.render(f"{change:+.2f}%", True, change_color)
            screen.blit(change_text, (currency_rect.right - 60, currency_rect.top + 10))

        screen.blit(code_text, (currency_rect.x + 15, currency_rect.y + 10))
        screen.blit(name_text, (currency_rect.x + 15, currency_rect.y + 40))
        screen.blit(rate_text, (currency_rect.x + 120, currency_rect.y + 20))

    # 绘制投资组合
    pygame.draw.rect(screen, PANEL_BG, (20, 570, 320, 120), border_radius=12)
    pygame.draw.rect(screen, HIGHLIGHT, (20, 570, 320, 120), 2, border_radius=12)

    portfolio_title = font_large.render("投资组合", True, HIGHLIGHT)
    screen.blit(portfolio_title, (30, 580))

    if player.portfolio:
        y_pos = 620
        for code, amount in player.portfolio.items():
            currency = next((c for c in currencies if c.code == code), None)
            if currency:
                value = amount * currency.rate
                port_text = font_small.render(f"{code}: {amount:.2f} (${value:.2f})", True, TEXT_COLOR)
                screen.blit(port_text, (40, y_pos))
                y_pos += 25
    else:
        empty_text = font_small.render("无持仓", True, TEXT_COLOR)
        screen.blit(empty_text, (40, 620))

    # 绘制汇率图表
    pygame.draw.rect(screen, PANEL_BG, (350, 140, 630, 250), border_radius=12)
    pygame.draw.rect(screen, HIGHLIGHT, (350, 140, 630, 250), 2, border_radius=12)

    chart_title = font_large.render("汇率走势", True, HIGHLIGHT)
    screen.blit(chart_title, (360, 150))

    if selected_currency:
        # 只显示选中的货币
        draw_line_chart(screen, 360, 180, 610, 200,
                        [selected_currency.history[-30:]],
                        [selected_currency.color],
                        [f"{selected_currency.code}/USD"])
    else:
        # 显示前三种货币
        draw_line_chart(screen, 360, 180, 610, 200,
                        [c.history[-30:] for c in currencies[:3]],
                        GRAPH_COLORS[:3],
                        [c.code for c in currencies[:3]])

    # 绘制市场事件
    pygame.draw.rect(screen, PANEL_BG, (350, 400, 630, 120), border_radius=12)
    pygame.draw.rect(screen, HIGHLIGHT, (350, 400, 630, 120), 2, border_radius=12)

    news_title = font_large.render("市场动态", True, HIGHLIGHT)
    screen.blit(news_title, (360, 410))

    if event_message and event_timer > 0:
        event_surf = font_medium.render(event_message, True, (255, 200, 100))
        screen.blit(event_surf, (370, 450))
    else:
        default_news = "市场稳定，无重大新闻"
        news_surf = font_medium.render(default_news, True, TEXT_COLOR)
        screen.blit(news_surf, (370, 450))

    # 绘制交易记录
    pygame.draw.rect(screen, PANEL_BG, (350, 530, 630, 160), border_radius=12)
    pygame.draw.rect(screen, HIGHLIGHT, (350, 530, 630, 160), 2, border_radius=12)

    trans_title = font_large.render("最近交易", True, HIGHLIGHT)
    screen.blit(trans_title, (360, 540))

    if player.transactions:
        # 显示最多3条交易记录
        for i, trans in enumerate(player.transactions[-3:]):
            trans_surf = font_small.render(trans, True, TEXT_COLOR)
            screen.blit(trans_surf, (370, 580 + i * 30))
    else:
        no_trans = font_small.render("暂无交易记录", True, TEXT_COLOR)
        screen.blit(no_trans, (370, 580))

    # 绘制按钮
    for button in buttons:
        button.check_hover(mouse_pos)
        button.draw(screen)

    # 绘制交易面板（如果激活）
    if trade_panel.active:
        trade_panel.draw(screen)

    # 绘制提示
    hint_text = font_small.render("选择一种货币进行交易，点击'下一天'推进市场变化", True, (150, 180, 220))
    screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT - 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()