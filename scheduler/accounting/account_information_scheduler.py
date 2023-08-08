from database.database import Database
from scheduler.accounting.abstract_accounting_scheduler import AbstractAccountingScheduler

class AccountInformationScheduler(AbstractAccountingScheduler):

    # 계좌 정보 스케줄러
    def __init__(self):
        self._worksheet = self._spreadsheet.get_worksheet(0)

    # 동기화 (Sheet -> DB)
    def synchronize(self):
        # sheet_data 업데이트
        self.update_sheet_data()

        # DB 업데이트
        database = Database()
        sql = "INSERT INTO data_map (category, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value = VALUES(value);"
        data = [item for item in self.sheet_data.items()]
        database.execute_many(sql, data)
        database.commit()
        database.close()

        # 현재 변수에 저장된 db_data 갱신
        self._db_data = self._sheet_data
    
    # 구글 시트에서 계좌 정보 읽어오기
    def _read_data_from_sheet(self):
        raw_data = self._worksheet.get_values()
        sheet_data = {}

        # 계좌 정보(계좌 번호, 은행, 예금주) 읽어오기
        i, j = self._find_index(raw_data, '계좌번호')
        sheet_data['account'] = raw_data[i][j + 1].strip()

        # 계좌 총액 읽어오기
        i, j = self._find_index(raw_data, '잔고 총액 : ')
        sheet_data['account_balance'] = raw_data[i][j + 1][1:].replace(',', '')

        return sheet_data
    
    def _read_data_from_database(self):
        # DB에서 데이터 읽기
        database = Database()
        sql = "SELECT * FROM data_map WHERE category = 'account' or category = 'account_balance';"
        raw_data = database.execute_all(sql)
        database.close()

        # 데이터를 형식에 맞게 변환
        db_data = {'account': None, 'account_balance': None}
        for data in raw_data:
            if data['category'] == 'account':
                db_data['account'] = data['value']
            else:
                db_data['account_balance'] = data['value']

        return db_data
