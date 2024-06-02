from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.database import Database
from datetime import datetime, timedelta
from utils.aes_cipher import AESCipher
from utils.api_access_level_tool import api_access_level

product = Namespace('product')
crypt = AESCipher()

@product.route("/<string:product_code>")
@product.response(200, 'Success')
@product.response(401, 'Unauthorized')
class Product(Resource):
    @api_access_level(1)
    @product.doc(security='apiKey')
    def get(self, product_code):
        database = Database()
        sql = "SELECT * FROM products WHERE code = %s;"
        values = (product_code,)
        product = database.execute_one(sql, values)
        
        if not product:     # 물품이 없을 때의 처리
            message = { 'message': '해당 물품이 존재하지 않아요 :(' }
            return message, 400

        product['status'] = { 'value': product['status'], 'rent_user': None }
            
        sql = "SELECT * FROM rent_list WHERE product_code = %s and return_day IS NULL;"
        values = (product['code'],)
        rent_log = database.execute_one(sql, values)
            
        if rent_log:
            sql = "SELECT name FROM users WHERE id = %s;"
            values = (rent_log['user_id'],)
            rent_user = database.execute_one(sql, values)
            product['status']['rent_user'] = crypt.decrypt(rent_user['name'])
        
        database.close()
        
        return product, 200

@product.route("/list")
@product.response(200, 'Success')
@product.response(401, 'Unauthorized')
class ProductList(Resource):
    @jwt_required()
    @product.doc(security='apiKey')
    def get(self):        
        database = Database()
        sql = "SELECT * FROM products;"
        product_list = database.execute_all(sql)
        
        for idx, product in enumerate(product_list):
            product_list[idx]['status'] = { 'value': product['status'], 'rent_user': None }
            
            sql = "SELECT * FROM rent_list WHERE product_code = %s and return_day IS NULL;"
            values = (product['code'],)
            rent_log = database.execute_one(sql, values)
            
            if rent_log:
                sql = "SELECT name FROM users WHERE id = %s;"
                values = (rent_log['user_id'],)
                rent_user = database.execute_one(sql, values)
                product_list[idx]['status']['rent_user'] = crypt.decrypt(rent_user['name'])
        
        database.close()
        
        if not product_list:
            message = { 'message': '물품이 존재하지 않아요 :(' }
            return message, 400
        else:
            return product_list, 200

@product.route("/list/<string:product_name>")
@product.response(200, 'Success')
@product.response(401, 'Unauthorized')
class SpecificProductList(Resource):
    @jwt_required()
    @product.doc(security='apiKey')
    def get(self, product_name):
        database = Database()
        sql = "SELECT * FROM products WHERE name LIKE %s;"
        values = (f"%{product_name}%",)
        product_list = database.execute_all(sql, values)
        
        for idx, product in enumerate(product_list):
            product_list[idx]['status'] = { 'value': product['status'], 'rent_user': None }
            
            sql = "SELECT * FROM rent_list WHERE product_code = %s and return_day IS NULL;"
            values = (product['code'],)
            rent_log = database.execute_one(sql, values)
            
            if rent_log:
                sql = "SELECT name FROM users WHERE id = %s;"
                values = (rent_log['user_id'],)
                rent_user = database.execute_one(sql, values)
                product_list[idx]['status']['rent_user'] = crypt.decrypt(rent_user['name'])
                
        database.close()
        
        if not product_list:
            message = { 'message': '해당 물품이 존재하지 않아요 :(' }
            return message, 400
        else:
            return product_list, 200

@product.route("/rent/<string:product_code>")
@product.response(200, 'Success')
@product.response(401, 'Unauthorized')
class RentProduct(Resource):
    @jwt_required()
    def post(self, product_code):
        user_id = get_jwt_identity()
        database = Database()
        sql = "SELECT * FROM products WHERE code = %s;"
        values = (product_code,)
        product = database.execute_one(sql, values)
        
        if product and product['is_available']: # 물품 대여에 대한 로직
            # 물품 정보를 대여중인 상태로 업데이트
            status = "대여중"
            sql = "UPDATE products SET is_available = %s, status = %s WHERE code = %s;"
            values = (0, status, product_code)
            database.execute(sql, values)
            database.commit()

            # 물품 대여 내역 추가
            now = datetime.now()
            rent_day = now.date()
            deadline = rent_day + timedelta(days=30)
            sql = "INSERT INTO rent_list(product_code, user_id, deadline, rent_day, return_day) "\
                "VALUES(%s, %s, %s, %s, NULL);"
            values = (product_code, user_id, deadline, rent_day)
            database.execute(sql, values)
            database.commit()

            # 물품 정보가 변경 되었으므로 물품 상세 정보 재조회
            sql = "SELECT * FROM products WHERE code = %s;"
            values = (product_code,)
            product_data = database.execute_one(sql, values)

            # 빌린 사람 이름 조회
            sql = "SELECT name FROM users WHERE id = %s;"
            values = (user_id,)
            rent_user = database.execute_one(sql, values)

            # 디데이 계산
            d_day = (deadline - rent_day).days

            # 물품 상태 정보 추가
            product_data['status'] = { 'value': status, 'rent_user': crypt.decrypt(rent_user['name']) }

            # 대여 정보에 물품 정보 모두 추가
            rent_data = { 'product': product_data }

            # 대여 관련 정보 추가
            rent_data['deadline'] = deadline.strftime('%Y-%m-%d')
            rent_data['rent_day'] = rent_day.strftime('%Y-%m-%d')
            rent_data['d_day'] = d_day
            rent_data['return_day'] = None

            database.close()
            return rent_data, 200
        else:
            database.close()
            message = {}
            if not product:
                message['message'] = '등록되지 않은 물품이에요 :('
                message['value'] = 0
            elif product['status'] == "대여중":
                message["message"] = '현재 대여중인 물품이에요 :('
                message['value'] = 1
            else:
                message['message'] = "현재 대여 불가능한 물품이에요 :("
                message['value'] = 2
            return message, 400

@product.route("/return/<string:product_code>")
@product.response(200, 'Success')
@product.response(401, 'Unauthorized')
class ReturnProduct(Resource):
    @jwt_required()
    @product.doc(security='apiKey')
    def put(self, product_code):
        user_id = get_jwt_identity()
        database = Database()
        sql = "SELECT * FROM products WHERE code = %s;"
        values = (product_code,)
        product = database.execute_one(sql, values)

        # 물품 반납에 대한 로직
        if product and not product['is_available']:
            if product['status'] == "대여중":
                # 맞는 대여 내역이 있는지 검증 
                sql = "SELECT * FROM rent_list "\
                    "WHERE product_code = %s and user_id = %s and return_day IS NULL;"
                values = (product_code, user_id)
                rent_data = database.execute_one(sql, values)
                if not rent_data:
                    return { 'message': '데이터가 올바르지 않아요 :(\n지속적으로 발생 시 문의해주세요!' }, 500
                
                # 물품 대여 내역에 반납일자 반영
                now = datetime.now()
                return_day = now.date()
                status = "대여 가능"
                sql = "UPDATE rent_list SET return_day = %s "\
                    "WHERE product_code = %s and user_id = %s and return_day IS NULL;"
                values = (return_day, product_code, user_id)
                database.execute(sql, values)
                database.commit()

                # 물품 정보 수정
                sql = "UPDATE products SET is_available = %s, status = %s WHERE code = %s;"
                values = (1, status, product_code)
                database.execute(sql, values)
                database.commit()

                # 물품 정보가 변경 되었으므로 물품 상세 정보 재조회
                sql = "SELECT * FROM products WHERE code = %s;"
                values = (product_code,)
                product_data = database.execute_one(sql, values)

                # 물품 상태 정보 추가
                product_data['status'] = { 'value': status, 'rent_user': None }

                # 반납 정보에 물품 정보 모두 추가
                return_data = { 'product': product_data }

                # 물품 정보에 대여 관련 정보 추가
                return_data['deadline'] = rent_data['deadline'].strftime('%Y-%m-%d')
                return_data['rent_day'] = rent_data['rent_day'].strftime('%Y-%m-%d')
                return_data['d_day'] = None
                return_data['return_day'] = return_day.strftime('%Y-%m-%d')

                database.close()

                return return_data, 200    
            else:
                database.close()
                return { 'message': '반납을 할 수 없는 물품이에요 :(' }, 400
        else:
            # 대여 가능한 경우
            database.close()
            return { 'message': '대여 중인 물품만 반납할 수 있어요 :(' }, 400
