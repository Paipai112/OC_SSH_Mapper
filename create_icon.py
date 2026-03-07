"""
生成应用图标
"""

from PIL import Image, ImageDraw

def create_icon():
    """创建应用图标"""
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []

    for size in sizes:
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 绘制圆形背景 (深蓝色)
        margin = size[0] // 8
        draw.ellipse(
            (margin, margin, size[0] - margin, size[1] - margin),
            fill=(0, 120, 212, 255)  # 蓝色
        )

        # 绘制隧道图标 (两条平行线和箭头)
        center_x = size[0] // 2
        center_y = size[1] // 2
        line_width = max(size[0] // 16, 2)

        # 左边入口
        left_start = margin + size[0] // 6
        # 右边出口
        right_end = size[0] - margin - size[0] // 6

        # 上线
        draw.line(
            (left_start, center_y - size[1] // 8, right_end, center_y - size[1] // 8),
            fill=(255, 255, 255, 255),
            width=line_width
        )

        # 下线
        draw.line(
            (left_start, center_y + size[1] // 8, right_end, center_y + size[1] // 8),
            fill=(255, 255, 255, 255),
            width=line_width
        )

        # 箭头 (表示数据流向)
        arrow_size = size[0] // 6
        draw.polygon(
            [
                (right_end, center_y),
                (right_end - arrow_size, center_y - arrow_size // 2),
                (right_end - arrow_size, center_y + arrow_size // 2)
            ],
            fill=(255, 255, 255, 255)
        )

        images.append(img)

    # 保存为ico文件
    images[0].save(
        'assets/icon.ico',
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )
    print("图标已创建: assets/icon.ico")

if __name__ == "__main__":
    import os
    os.makedirs('assets', exist_ok=True)
    create_icon()