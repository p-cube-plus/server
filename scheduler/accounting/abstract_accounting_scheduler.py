from abc import abstractmethod, ABCMeta
import gspread # 5.10.0
from datetime import datetime, date

class AbstractAccountingScheduler(metaclass=ABCMeta):
    # 구글 시트 연결 및 변수 선언
    _client = gspread.service_account(filename= "scheduler/accounting/service_account.json")
    _spreadsheet = _client.open_by_url("https://docs.google.com/spreadsheets/d/1Ck5pB9Wm-d0uHJzoSCNH8TxopH_CrjMIR-_1FMqZpwg/edit?usp=sharing")
    _worksheet = None
    _sheet_data = None
    _db_data = None

    # 관련 로직 추후 구현 예정
    _last_update = None
    _last_synchronization = None

    @property # 구글 시트 데이터
    def sheet_data(self):
        if not self._sheet_data:
            self.update_sheet_data()
        return self._sheet_data
    
    @property # DB 데이터
    def db_data(self):
        if not self._db_data:
            self.update_db_data()
        return self._db_data
    
    # 동기화 (Sheet -> DB)
    @abstractmethod
    def synchronize(self, *args):
        pass

    # 구글 시트 데이터 갱신
    def update_sheet_data(self, *args):
        self._sheet_data = self._read_data_from_sheet(*args)

    # DB 데이터 갱신
    def update_db_data(self, *args):
        self._db_data = self._read_data_from_database(*args)

    # 구글 시트로부터 데이터 읽어오기
    @abstractmethod
    def _read_data_from_sheet(self, *args):
        pass

    # DB로부터 데이터 읽어오기
    @abstractmethod
    def _read_data_from_database(self, *args):
       pass
    
    # 데이터에서의 특정 값의 위치 반환
    def _find_index(self, data, value):
        for i, row in enumerate(data):
            for j, cell in enumerate(row):
                if cell == value:
                    return i, j
        return None
        
    # 부분 테이블 반환
    def _get_sub_data(self, data, start_row, start_col, end_row, end_col):
        return [row[start_col : end_col] for row in data[start_row : end_row]]
    
    # 달(month)을 YYYY-MM-01 형식으로 변환
    def _get_date_by_month(self, current_date, month):
        return date(current_date.year - int(current_date.month < 3) + int(month > 12), month if month <= 12 else month - 12, 1)