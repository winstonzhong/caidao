
import xml.etree.ElementTree as ET

def xml_to_dict(element):
    result = {}
    for child in element:
        sub_dict = xml_to_dict(child)
        if len(sub_dict) == 1 and 'text' in sub_dict.keys():
            sub_dict = sub_dict.get('text')
        if child.tag in result:
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(sub_dict)
        else:
            result[child.tag] = sub_dict
    if element.text and element.text.strip():
        result['text'] = element.text
    return result

def 解析xml字符串(txt):
    return xml_to_dict(ET.fromstring(txt))


if __name__ == "__main__":
    tmp_test = '''
    <xml><ToUserName><![CDATA[gh_491de88dfc6e]]></ToUserName>
    <FromUserName><![CDATA[orRSd5627bsdWuYE8EgUkpD7knLY]]></FromUserName>
    <CreateTime>1732329909</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[最新资讯]]></Content>
    <MsgId>24801004976846051</MsgId>
    <bizmsgmenuid>101</bizmsgmenuid>
    </xml>
    '''
    print(解析xml字符串(tmp_test))    