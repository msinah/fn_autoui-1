import pytest
from unit_tools.handle_data.read_data import data
from configs.setting import FILE_PATH
from unit_tools.assert_control import *
import os


data_path = FILE_PATH['data']
cases_dict = data.load_yaml(os.path.join(data_path,'login.yaml'))

class Testfbmcart:
    @pytest.mark.skipif(cases_dict['loginpage'][0]['skip'] == True, reason='跳过执行')
    @pytest.mark.parametrize('CaseData', cases_dict['loginpage'])
    def test_login(self,page, run_case_fixture, CaseData):
        run_case_fixture(page, CaseData)
        try:
            # page.wait_for_timeout(1000)
            page.pause()
            # 保存cookies
            cookies_path = FILE_PATH['set_cookies']
            page.context.storage_state(path=cookies_path)
        except Exception as e:
            print(f'结果错误{e}')
            raise