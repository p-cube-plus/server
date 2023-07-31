from database.database import Database
from datetime import datetime, date
from scheduler.accounting.abstract_accounting_scheduler import AbstractAccountingScheduler

class AccountingScheduler(AbstractAccountingScheduler):
    # 거래 내역 스케줄러
    def __init__(self):
        self._worksheet = self._spreadsheet.get_worksheet(1)

    # 동기화 (Sheet -> DB)
    def synchronize(self):
        pass

    # 구글 시트에서 거래 내역 데이터를 읽어오기
    def _read_data_from_sheet(self):
        raw_data = self._worksheet.get_values()
        read_data = []

        # 수입 내역 읽어오기
        i, j = self._find_index(raw_data, '수입')
        i += 3
        while(i < len(raw_data) and self._is_date(raw_data[i][j])):
            row = raw_data[i][j : j + 5]
            # 데이터를 형식에 맞게 변환
            row[0] = row[0].replace('.', '-')
            row[1] = int(row[1][1:].replace(',', ''))
            read_data.append(row)
            i += 1
        
        # 지출 내역 읽어오기
        i, j = self._find_index(raw_data, '지출')
        i += 3
        while(i < len(raw_data) and self._is_date(raw_data[i][j])):
            row = raw_data[i][j : j + 3] + raw_data[i][j + 4 : j + 6]
            # 데이터를 형식에 맞게 변환
            row[0] = row[0].replace('.', '-')
            row[1] = -int(row[1][1:].replace(',', ''))
            read_data.append(row)
            i += 1

        read_data.sort()
        return read_data
    
    # DB에서 거래 내역 데이터 읽어오기
    def _read_data_from_database(self, current_date = datetime.today()):
        # 구글 시트에서 3월 ~ 다음 해 2월까지의 데이터를 유지하기 때문에, DB에서도 이에 맞춰서 데이터를 읽어 온다.
        current_month = current_date.month

        start_date = date(current_date.year, 3, 1)
        end_date = date(current_date.year + 1, 2, 1)

        if current_month < 3:
            start_date.year -= 1
            end_date.year -= 1

        # 각 date를 문자열로 변환
        start_date.strftime('%Y-%m-%d')
        end_date.strftime('%Y-%m-%d')
        
        database = Database()

        # DB에서 기간에 따른 데이터 불러오기
        sql = "SELECT date, amount, description, category, payment_method, id FROM accountings "\
            f"WHERE date between '{start_date}' and '{end_date}' ORDER BY date;"

        raw_data = database.execute_all(sql)
        database.close()

        # 데이터를 구글 시트 데이터 형식에 맞게 처리
        db_data = []
        for row in raw_data:
            row['date'] = row['date'].strftime('%Y-%m-%d')
            db_data.append(list(row.values()))
        return db_data
    
    # 문자열이 날짜 형식인지 확인
    def _is_date(self, string, date_format = "%Y.%m.%d"):
        try:
            datetime.strptime(string, date_format)
            return True
        except ValueError:
            return False