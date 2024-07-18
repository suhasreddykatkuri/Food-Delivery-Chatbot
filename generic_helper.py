import re
def extract_session_id(session_str):
    match = re.search('sessions\W(\S+)\Wcontexts',session_str)
    if match:
        return match.group(1)
    return ''
if __name__=="__main__":
    print(extract_session_id("projects/rhino-wbbf/agent/sessions/27c5d8e1-e0a3-ac76-4d64-013d41b50601/contexts/ongoing-order"))