import asyncio
import json

import requests
from asgiref.sync import async_to_sync
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import os

from rest_framework.views import APIView

from .filters import GoodsFilter
from django_filters import rest_framework as filters
from .pagination import CustomPagination, AllObjectPagination
from .utils import BusinessRuService, BusinessRuAPIClient
from rest_framework import generics
from rest_framework.viewsets import ModelViewSet
from .models import GoodsModel, GroupOfGoods
from .serializers import GoodsSerializer, GroupOfGoodsSerializer
from django.http import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiohttp import web

load_dotenv()

token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')


bot = Bot(token=token)

keyboard = types.InlineKeyboardMarkup().add(InlineKeyboardButton(text='Обработано✅', callback_data='handle'))


class GoodsAPIView(ModelViewSet):
    queryset = GoodsModel.objects.all().distinct()
    serializer_class = GoodsSerializer
    pagination_class = CustomPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = GoodsFilter


class GroupListAPIView(generics.ListAPIView):
    queryset = GroupOfGoods.objects.order_by('id')
    serializer_class = GroupOfGoodsSerializer
    pagination_class = AllObjectPagination


@method_decorator(csrf_exempt, name='dispatch')
class Checkout(View):
    def post(self, request):
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                print(data)

                message_text = 'ЗАКАЗ С САЙТА:\n'
                if data['consult']:
                    message_text += f"Консультация - @{data['telegram_nickname']}"
                    n = async_to_sync(bot.send_message)(chat_id=chat_id, text=message_text, reply_markup=keyboard)
                else:
                    for good in data['basket']:
                        message_text += f'{good["title"]} - {good["count"]}шт - {good["price"]}₩\n'
                    message_text += f'{data["first_name"]} {data["second_name"]}\n' \
                                    f'Электронная почта - {data["email"]}\n' \
                                    f'Инстаграм - {data["inst"]}\n' \
                                    f'Город - {data["city"]}\n' \
                                    f'Тип клиента - {data["client_type"]}\n' \
                                    f'{data["phone"]} - @{data["telegram_nickname"]}'

                    n = async_to_sync(bot.send_message)(chat_id=chat_id, text=message_text, reply_markup=keyboard)
                return JsonResponse({'message': 'DONE!'}, status=200)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Некорректный формат JSON'}, status=400)
        else:
            return JsonResponse({'error': 'Запрос должен содержать данные JSON'}, status=400)


def update_data(request):
    b = BusinessRuService()
    b.group_to_model()
    b.goods_to_model()
    return HttpResponse(content='Data updated!', status=200)


def get_all_goods(request):
    mast_point = GoodsSerializer(GoodsModel.objects.all(), many=True).data
    data = {'result': mast_point}
    # out.write(json.dumps(data, ensure_ascii=False))
    return JsonResponse(data, safe=False)
