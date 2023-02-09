from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database

project = Namespace('project')

@project.route("/list")
class ProjectListAPI(Resource):
    def get(self):
        # 데이터베이스에서 프로젝트 목록을 불러옴
        database = Database()
        sql = f"SELECT * FROM projects;"
        project_list = database.execute_all(sql)
        
        if not project_list:    # 프로젝트가 하나도 없을 때의 처리
            database.close()
            
            return [], 200
        else:
            for idx, value in enumerate(project_list):
                # 날짜를 문자열 날짜로 변경
                project_list[idx]['start_date'] = value['start_date'].strftime('%Y/%m/%d')
                project_list[idx]['end_date'] = value['end_date'].strftime('%Y/%m/%d')
                
                # 팀원 모집 여부와 문의 가능 여부를 Boolean 값으로 변경
                project_list[idx]['is_finding_member'] = True if value['is_finding_member'] else False
                project_list[idx]['is_able_inquiry'] = True if value['is_able_inquiry'] else False
                
                # 프로젝트 팀원 수 추가
                sql = f"SELECT count(*) from project_members where project_id = {value['id']};"
                member_count = database.execute_one(sql)
                project_list[idx]['member_count'] = member_count['count(*)']
                
            return project_list, 200

@project.route('/<int:id>')
class ProjectDetailAPI(Resource):
    def get(self, id):
        # 데이터베이스에서 id 값에 맞는 프로젝트 상세 내역을 불러옴
        database = Database()
        sql = f"SELECT * FROM projects where id = {id};"
        project = database.execute_one(sql)
        
        if not project:
            database.close()
            return { 'message': '프로젝트 식별자가 올바르지 않아요 :(' }, 400
        else:
            # 날짜를 문자열 날짜로 변경
            project['start_date'] = project['start_date'].strftime('%Y/%m/%d')
            project['end_date'] = project['end_date'].strftime('%Y/%m/%d')
                
            # 팀원 모집 여부와 문의 가능 여부를 Boolean 값으로 변경
            project['is_finding_member'] = True if project['is_finding_member'] else False
            project['is_able_inquiry'] = True if project['is_able_inquiry'] else False
            
            # 프로젝트 팀원 목록의 id 조회
            sql = f"SELECT user_id from project_members where project_id = {project['id']};"
            user_id_list = database.execute_all(sql)
            user_list = []
            # 프로젝트에 속하는 팀원들의 상세 정보를 구하여 리스트에 추가
            for id_value in user_id_list:
                user_id = id_value['user_id']
                sql = f"SELECT * from users where id = {user_id};"
                row = database.execute_one(sql)
                user_list.append(row)
            
            # 프로젝트 팀원 목록 추가
            project['members'] = user_list
            database.close()
            
            return project, 200

@project.route('/<int:id>/modify')
class ProjectEditAPI(Resource):
    def put(self):
        """
        user_id
        is_finding_member
        """
        body_data = request.get_json()
        user_id = body_data['user_id']
        is_finding_member = body_data['is_finding_member']
        
        sql = f"SELECT  FROM users where id = {user_id};"
        # 유저가 PM이면 설정할 수 있게
        # PM이 아니면 안되게
        
        # DB 수정 후 마저 구현 예정
        return {}