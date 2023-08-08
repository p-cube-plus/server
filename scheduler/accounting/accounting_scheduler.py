from database.database import Database
from datetime import datetime, date
from scheduler.accounting.abstract_accounting_scheduler import AbstractAccountingScheduler

# payment_method(결제 수단)
PAYMENT_METHOD = {0: '통장', 1: '금고'}

class AccountingScheduler(AbstractAccountingScheduler):

    # 거래 내역 스케줄러
    def __init__(self):
        self._worksheet = self._spreadsheet.get_worksheet(1)

    # 동기화 (Sheet -> DB)
    # 거래 장부에 데이터와 함께 id값이 존재한다고 가정하고 코드를 작성하였음. (추후 수정 예정)
    def synchronize(self):
        # 동기화에 앞서 data 업데이트
        self.update_sheet_data()
        current_date = datetime.today()
        self.update_db_data(current_date)

        sheet_idx = 0
        db_idx = 0

        created = [] # sheet_data의 index를 저장
        deleted = [] # db_data의 index를 저장
        modified = [] # sheet_data의 index를 저장

        # 데이터를 비교한다.
        while sheet_idx < len(self.sheet_data) and db_idx < len(self.db_data):
            sheet_data = self.sheet_data[sheet_idx]
            db_data = self.db_data[db_idx]

            # 데이터가 구글 시트에만 존재할 때
            if sheet_data[0] < db_data[0]:
                created.append(sheet_idx)
                sheet_idx += 1
                continue
            # 데이터가 DB에만 존재할 때
            elif sheet_data[0] > db_data[0]:
                deleted.append(db_idx)
                db_idx += 1
                continue
            # id가 일치하는 데이터를 찾았을 때
            else:
                # 데이터가 다를 때
                if sheet_data != db_data:
                    modified.append(sheet_idx)
                sheet_idx += 1
                db_idx += 1

        # 남은 구글 시트 데이터가 있을 때
        while sheet_idx < len(self.sheet_data):
            created.append(sheet_idx)
            sheet_idx += 1
        
        # 남은 DB 데이터가 있을 때
        while db_idx < len(self.db_data):
            deleted.append(db_idx)
            db_idx += 1

        database = Database()

        # 새로 추가된 데이터를 INSERT
        sql = "INSERT INTO accountings VALUES(%s, %s, %s, %s, %s, %s);"
        values = []

        for sheet_idx in created:
            value = tuple(self.sheet_data[sheet_idx])
            values.append(value)


        database.execute_many(sql, values)

        # 삭제된 데이터를 DELETE
        sql = "DELETE FROM accountings WHERE id = %s;"
        values = []

        for db_idx in deleted:
            value = (self.db_data[db_idx][0], )
            values.append(value)

        database.execute_many(sql, values)

        # 수정된 데이터를 UPDATE
        sql = "UPDATE accountings SET date = %s, amount = %s, description = %s, category = %s, payment_method = %s WHERE id = %s;"
        values = []

        for sheet_idx in modified:
            value = tuple(self.sheet_data[sheet_idx][1:] + [self.sheet_data[sheet_idx][0]])
            values.append(value)

        database.execute_many(sql, values)

        database.commit()
        database.close()

        # 현재 변수에 저장된 db_data 갱신
        self._db_data = self._sheet_data

    # 구글 시트에서 거래 내역 데이터를 읽어오기
    def _read_data_from_sheet(self):
        raw_data = self._worksheet.get_values()
        sheet_data = []

        # 지출 내역 읽어오기
        i, j = self._find_index(raw_data, '지출')
        i += 3
        while(i < len(raw_data) and self._is_date(raw_data[i][j])):
            row = raw_data[i][j : j + 5]
            # 데이터를 형식에 맞게 변환
            row[0] = row[0].replace('.', '-')
            row[1] = -int(row[1][1:].replace(',', ''))
            row[-1] = self._convert_to_index(PAYMENT_METHOD, row[-1])

            sheet_data.append(row)
            i += 1

        # 수입 내역 읽어오기
        i, j = self._find_index(raw_data, '수입')
        i += 3
        while(i < len(raw_data) and self._is_date(raw_data[i][j])):
            row = raw_data[i][j : j + 3] + raw_data[i][j + 4 : j + 6]
            # 데이터를 형식에 맞게 변환
            row[0] = row[0].replace('.', '-')
            row[1] = int(row[1][1:].replace(',', ''))
            row[-1] = self._convert_to_index(PAYMENT_METHOD, row[-1])
            sheet_data.append(row)
            i += 1

        sheet_data.sort()

        # 임시 코드(id값 임의 삽입)
        for idx, row in enumerate(sheet_data):
            row.insert(0, idx + 1)

        return sheet_data
    
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
        sql = "SELECT * FROM accountings "\
            f"WHERE date between '{start_date}' and '{end_date}' ORDER BY id;"

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
    
    # 문자열 데이터를 index로 변경
    def _convert_to_index(self, dictionary, string):
        for key, value in dictionary.items():
            if value == string:
                return key
        return None