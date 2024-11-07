import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import hashlib
import re

from notion.members import Members
from database.database import Database
from utils.aes_cipher import AESCipher
from utils.user_tool import UserTool

class UserSync:
    def __init__(self):
        self.pcube_members = None
        self.warnings_info = ['warnings', 'half_warnings', 'total_warnings']

    def sync_users(self):
        if not self.pcube_members:
            raise ValueError("load_pcube_members()를 먼저 호출하여 데이터를 불러와주세요.")
        
        # 전화번호가 없는 정보 제거
        members = [data for data in self.pcube_members
                         if data['phone_number'] is not None and data['phone_number'] != '']
        
        # 유저 관련 정보만 얻기
        for data in members:
            for key in self.warnings_info:
                del data[key]
                
        # 삽입 전 데이터 전처리
        crypt = AESCipher()
        for data in members:
            # 휴대폰 번호 ###-####-#### 형태로 변경
            data['phone_number'] = re.sub(r'\D', '', data['phone_number'])
            data['phone_number'] = re.sub(r'(\d{3})(\d{4})(\d{4})', r'\1-\2-\3', data['phone_number'])
            
            # 식별자의 경우 식별자가 있을 경우, 그대로 사용하고 없으면 암호화하여 생성
            data['id'] = data['id'] if data['id'] is not None and data['id'] != '' else hashlib.sha256(str(data['name'] + data['phone_number']).encode('utf-8')).hexdigest()
            
            # 그 외의 데이터 암호화
            data['name'] = crypt.encrypt(str(data['name']))
            data['univ'] = crypt.encrypt(str(data['univ']))
            data['etc_message'] = crypt.encrypt(str(data['etc_message']))
            data['absent_reason'] = crypt.encrypt(str(data['absent_reason']))
            data['absent_detail_reason'] = crypt.encrypt(str(data['absent_detail_reason']))
            data['phone_number'] = crypt.encrypt(str(data['phone_number']))
            data['major'] = crypt.encrypt(str(data['major']))
            data['student_id'] = crypt.encrypt(str(data['student_id']))
            
            # INT를 사용하는 데이터는 index로 변환
            data['rank'] = UserTool.rank_to_index(data['rank'])
            data['part'] = UserTool.part_to_index(data['part'])
            data['rest_type'] = UserTool.rest_type_to_index(data['rest_type'])
            
            data['grade'] = -1 if data['grade'] is None else data['grade']
        
        # SQL Insert 작업을 위해 데이터 형식 맞춰주기
        members = [tuple(data.values()) for data in members]
        if not members:
            raise ValueError("데이터가 올바르지 않아요 :(")
        columns = ['id', 'name', 'level', 'grade', 'part_index',
                   'univ', 'last_cleaning', 'rest_type', 'etc_message',
                   'absent_reason', 'absent_detail_reason', 'phone_number',
                   'join_date', 'birth_date', 'birth_month', 'birth_day',
                   'major', 'student_id', 'is_next_birth', 'return_plan_date',
                   'workshop_count', 'gogoma']
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        updates = ', '.join([f'{col}=VALUES({col})' for col in columns if col != 'id'])
        
        # 유저 정보 동기화
        database = Database()
        sql = f"INSERT INTO user ({columns_str}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates};"
        database.execute_many(sql, members)
        database.commit()
        
        # 탈퇴자 조회 후 모든 데이터 제거
        sql = f"DELETE FROM user WHERE level = {UserTool.rank_to_index('탈퇴자')};"
        database.execute(sql)
        database.commit()
        database.close()
        
        print('sync_user() finished.')
    
    def load_pcube_members(self, target_ranks=None):
        self.pcube_members = Members.get_targets(target_ranks=target_ranks)

if __name__ == '__main__':
    user_sync = UserSync()
    user_sync.load_pcube_members()
    user_sync.sync_users()
