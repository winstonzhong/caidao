'''
Created on 2024年1月22日

@author: lenovo
'''
from tool_xpath import find_by_xpath

def get_last_chat_item(adb_device):
    x = '//android.widget.LinearLayout[re:match(@resource-id, ".*/chat_item")]/android.widget.TextView'
    e = find_by_xpath(adb_device, x)
    e.wait()
    return e.all()[-1]

def get_play_button_pop(adb_device):
    '''
    >>> get_play_button_pop(DummyDevice('ut/play_button.xml')).wait().bounds
    (682, 509, 743, 570)
    '''
    # '//com.lynx.tasm.behavior.ui.LynxFlattenUI[@text="搜索"]/preceding-sibling::*'
    # text="语音朗读" resource-id="com.larus.nova:id/menu_text" class="android.widget.TextView"
    # resource-id="com.larus.nova:id/menu_icon" class="android.widget.ImageView"
    x = '//android.widget.TextView[re:match(@resource-id, ".*/menu_text")][@text="语音朗读"]/following-sibling::android.widget.ImageView[re:match(@resource-id, ".*/menu_icon")]'
    return find_by_xpath(adb_device, x)

def is_page_not_finished(adb_device):
    '''
    >>> is_page_not_finished(DummyDevice('ut/finished1.xml'))
    False
    >>> is_page_not_finished(DummyDevice('ut/finished_no_like_action.xml'))
    False
    >>> is_page_not_finished(DummyDevice('ut/finished2.xml'))
    False
    >>> is_page_not_finished(DummyDevice('ut/not_finished1.xml'))
    True
    >>> is_page_not_finished(DummyDevice('ut/not_finished2.xml'))
    True
    '''
    x = '//android.widget.LinearLayout[re:match(@resource-id, ".*/msg_action_like")]'
    e = find_by_xpath(adb_device, x).wait()
    if e is not None:
        return False
    txt = get_last_chat_item(adb_device).text
    return txt.endswith('⚫')


if __name__ == "__main__":
    import doctest
    from tool_xpath import DummyDevice
    print(doctest.testmod(verbose=False, report=False))
