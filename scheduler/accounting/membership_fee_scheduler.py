
from database.database import Database
from datetime import datetime, date
from scheduler.accounting.abstract_accounting_scheduler import AbstractAccountingScheduler

class MembershipFeeScheduler(AbstractAccountingScheduler):
    # 월별 회비 확인표 스케줄러
    def __init__(self):
        self._worksheet = self._spreadsheet.get_worksheet(2)

    # 동기화 (Sheet -> DB)
    def synchronize(self):
        # 동기화에 앞서 data 업데이트
        self.update_sheet_data()
        current_date = datetime.today()
        self.update_db_data(current_date)

        sheet_idx = 0
        db_idx = 0

        created = [] # sheet_data의 index를 저장
        deleted = [] # db_data의 index를 저장

        # (i, j) 형식으로 저장됨에 유의
        modified = [] # sheet_data의 index를 저장

        # 대응되는 user_id를 찾은 후 category 정보를 비교한다.
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
            # user_id가 일치하는 데이터를 찾았을 때
            else:
                for i in range(12):
                    # category가 변경되었는지 검사
                    if sheet_data[i + 2] != db_data[i + 2]:
                        modified.append((sheet_idx, i + 2))
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
        sql = "INSERT INTO membership_fees (`date`, user_id, category, amount) VALUES(%s, %s, %s, %s);"
        values = []

        for sheet_idx in created:
            created_data = self.sheet_data[sheet_idx]
            print(created_data)
            for idx, category in enumerate(created_data[2:]):
                monthly_date = self._get_date_by_month(current_date, idx + 3)
                value = (monthly_date, created_data[0], category, created_data[1] if category < 5 else 0)
                values.append(value)

        database.execute_many(sql, values)

        # 삭제된 데이터를 DELETE
        sql = "DELETE FROM membership_fees WHERE user_id = %s;"
        values = []

        for db_idx in deleted:
            deleted_data = self.db_data[db_idx]
            value = (deleted_data[0], )
            values.append(value)

        database.execute_many(sql, values)

        # 수정된 데이터를 UPDATE
        sql = "UPDATE membership_fees SET category = %s WHERE `date` = %s AND user_id = %s;"
        values = []

        for sheet_idx, pos in modified:
            modified_data = self.sheet_data[sheet_idx]
            monthly_date = self._get_date_by_month(current_date, pos + 1)
            value = (modified_data[pos], monthly_date, modified_data[0])
            values.append(value)

        database.execute_many(sql, values)

        database.commit()
        database.close()

        # 현재 변수에 저장된 db_data 갱신
        self._db_data = self._sheet_data

    # 현재는 이름을 읽어오지만 추후 user_id로 변환하도록 수정 예정
    # 구글 시트에서 회비 납부 데이터를 읽어오기
    def _read_data_from_sheet(self):
        raw_data = self._worksheet.get_values()
        read_data = self._read_data_from_sheet_by_level(raw_data, '정회원') + self._read_data_from_sheet_by_level(raw_data, '수습회원')
        read_data.sort()
        return read_data
    
    # 구글 시트에서 회원 등급별로 회비 납부 데이터를 읽어오기
    def _read_data_from_sheet_by_level(self, raw_data, level):
        index = self._find_index(raw_data, level)
        member_count = int(raw_data[index[0] + 1][index[1]][:-1])
        sheet_data = self._get_sub_data(raw_data, index[0] + 3, index[1], index[0] + 3 + member_count, index[1] + 14)

        # 회비 금액 설정
        for row in sheet_data:
            for i, value in enumerate(row):
                if i < 2:
                    continue
                if value >= '0' and value <= '9':
                    row[i] = int(value)
                elif value == '-':
                    row[i] = 5
                else:
                    row[i] = 4
            row[1] = 3000 if level == '정회원' and row[1] == '4학년' else 5000

        return sheet_data
    
    # DB에서 회비 납부 데이터 읽어오기
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
        sql = "SELECT user_id, GROUP_CONCAT(amount ORDER BY date) as amounts, GROUP_CONCAT(category ORDER BY date) as categories FROM membership_fees "\
            f"WHERE date between '{start_date}' and '{end_date}' GROUP BY user_id ORDER BY user_id;"

        raw_data = database.execute_all(sql)
        database.close()

        # 데이터를 구글 시트 데이터 형식에 맞게 처리
        db_data = []
        for row in raw_data:
            db_data.append([row['user_id'], int(row['amounts'].split(',')[-1])])
            db_data[-1].extend(map(int, row['categories'].split(',')))
        return db_data