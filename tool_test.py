raw = """
https://file.j1.sale/api/file/test/blood_sugar_5.png
https://file.j1.sale/api/file/test/blood_sugar_52.png
https://file.j1.sale/api/file/test/blood_sugar_54.png
https://file.j1.sale/api/file/test/blood_sugar_55.png
https://file.j1.sale/api/file/test/blood_pressure_1.png
https://file.j1.sale/api/file/test/blood_pressure_102.png
https://file.j1.sale/api/file/test/blood_pressure_82.png
https://file.j1.sale/api/file/test/lunch_1.jpg
https://file.j1.sale/api/file/test/lunch_2.jpg
https://file.j1.sale/api/file/test/lunch_3.jpg
https://file.j1.sale/api/file/test/lunch_4.jpg
https://file.j1.sale/api/file/test/lunch_5.jpg
"""


img_understand_output = {
    "output": {
        "https://file.j1.sale/api/file/test/blood_pressure_1.png": "图中展示的是一个电子血压计。它的屏幕上清晰地显示着血压值，高压为135，低压为94。此外，它还有脉搏/分钟、用户切换、记忆、开始/停止等按钮。整个电子血压计外观简洁，便于操作。",
        "https://file.j1.sale/api/file/test/blood_pressure_102.png": "图中展示的是一个电子血压计。它的屏幕上显示着血压值和脉搏值，分别为高压 129 mmHg、低压 84 mmHg、脉搏 91 次/分钟。同时，屏幕上还显示“血压正常”和“缠绕正确”。此外，电子血压计的右侧有两个按钮，分别是“开始/停止”按钮和“A/B”按钮。整个电子血压计的设计简洁大方，便于使用。",
        "https://file.j1.sale/api/file/test/blood_pressure_82.png": "图中展示的是一个电子血压计。它的屏幕上清晰地显示着血压值，高压为\\(121\\)，低压为\\(84\\)，脉搏为\\(79\\)，日期为\\(8-16\\)，电量为\\(57\\%\\)。仪器整体为米白色，右侧有一个开关，下方有开始和停止两个按钮。该血压计的设计简洁大方，便于操作和读数。",
        "https://file.j1.sale/api/file/test/blood_sugar_5.png": "图中展示的是一个血糖仪。画面中是一个人的手拿着一个白色的血糖仪，旁边是一个针管。屏幕上显示着“9.1 mmol/L”，意思是当前的血糖值为9.1毫摩尔/升。画面给人一种干净、整洁的感觉。",
        "https://file.j1.sale/api/file/test/blood_sugar_52.png": "图中展示的是一个血糖仪。这个血糖仪呈白色，上面印有“OMRON”的字样。目前屏幕上显示着“5.0 mmol/L”，还有“01:02”的字样。这个血糖仪的设计简洁，便于携带。",
        "https://file.j1.sale/api/file/test/blood_sugar_54.png": "图中展示的是一个血糖仪。这个血糖仪呈白色，上面有黑色的“OMRON”字样。目前屏幕上显示着数字“7.4”，可能代表血糖值。图片较为模糊，无法看清楚其他的细节。",
        "https://file.j1.sale/api/file/test/blood_sugar_55.png": "图中展示的是一个血糖仪。它的屏幕上清晰地显示着“5.5 mmol/L”，下方还有“低血糖”字样。此外，屏幕上还有电池图标和温度计图案。整个屏幕以绿色为底色，与黑色边框形成鲜明对比。",
        "https://file.j1.sale/api/file/test/lunch_1.jpg": "这是一张摆放在木质桌面上的美食图片。图片中心是一条蒸熟的鱼，鱼身上淋有汤汁，鱼身上还撒有葱花、香菜和花生米。鱼的周围摆放着四个菜和一碗汤。\n\n从左上角顺时针看，第一个是一盘炒豆角，豆角翠绿，上面还点缀着一些肉片；第二个是一盘炒白菜，白菜片洁白；第三个是一盘汤，里面有玉米、胡萝卜、肉丸和一些绿色的香菜；第四个是一盘炒四季豆，四季豆油亮，上面也撒有肉片。\n\n整体来看，这是一顿丰盛的家常便饭，色彩搭配鲜明，让人食欲大开。",
        "https://file.j1.sale/api/file/test/lunch_2.jpg": "这是一张摆放着四道菜的餐桌照片。从左上角顺时针看，第一道菜是清炒油麦菜，绿色的菜叶上撒着一些白色的蒜末，看起来鲜嫩可口；第二道菜是白米饭，颗粒分明，色泽洁白；第三道菜是红烧肉，肉块色泽红亮，表面覆盖着酱汁，看起来十分诱人；最后一道菜也是白米饭，与第一碗米饭相似。\n\n整体来看，这是一顿丰盛的中式家常餐，色彩搭配和谐，菜品看起来新鲜美味。",
        "https://file.j1.sale/api/file/test/lunch_3.jpg": "这是一张摆放在桌面上的美食图片。图片左侧是一盘红烧鱼，鱼的表面覆盖着红亮的酱汁，上面点缀着几颗红色的辣椒，鱼的旁边摆放着一双筷子。图片中间是一盘炒鸡蛋和蘑菇，鸡蛋呈金黄色，蘑菇是灰褐色，两者混合在一起，上面撒有绿色的葱花和红色的辣椒，看起来色彩鲜艳，让人食欲大开。图片右侧是两碗白米饭，米饭颗颗分明，看上去松软可口。\n\n整体来看，这是一顿丰盛的中式家常餐，包含了主食、荤菜和素菜，色彩搭配和谐，给人一种温馨舒适的感觉。",
        "https://file.j1.sale/api/file/test/lunch_4.jpg": "这是一张摆放在木质桌面上的餐点照片。从左到右，第一个盘子里装着一些切片的生菜，旁边是一个印有“Mr. Pizza”字样的白色盘子，里面装着一些白色的米饭。第二个盘子中装着炒鸡蛋和青椒，颜色金黄和翠绿相间，看起来十分诱人。第三个盘子里装着炒菠菜，颜色鲜绿，与炒鸡蛋和青椒形成对比。整体来看，这是一顿色彩丰富、营养均衡的餐点。",
        "https://file.j1.sale/api/file/test/lunch_5.jpg": "这是一个中式美食拼盘，包含了多种不同的菜肴。\n\n从左上角顺时针看，第一道菜是炒饭，米饭中混有鸡蛋和胡萝卜丁，表面撒有芝麻和葱花。旁边是糖醋里脊，肉片裹有面糊炸至金黄，上面淋有红色的酸甜酱汁。接下来是清蒸鱼，鱼肉洁白，上面放有葱丝和姜丝，淋有酱油。旁边是炒蔬菜，包括花菜、白菜和黄瓜，颜色翠绿。最下面是一碗汤，里面有肉片、豆腐和绿色的香菜。\n\n这些菜肴摆放在一个白色的盘子上，颜色鲜艳，看起来非常诱人。整体来看，这是一顿丰盛的中式餐点，包含了主食、肉类、蔬菜和汤品。",
    }
}


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            list(
                map(lambda x: x.strip(), filter(lambda x: x.strip(), raw.splitlines()))
            ),
            indent=3,
        )
    )
