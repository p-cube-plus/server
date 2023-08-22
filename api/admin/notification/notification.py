from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date

notification = Namespace('notification')