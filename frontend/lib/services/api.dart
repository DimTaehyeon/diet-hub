import 'package:dio/dio.dart';
import '../config.dart';
import '../models/diet.dart';

// 백엔드 API 호출 모음 (초보자용: 함수 하나 = API 하나)
class ApiService {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: AppConfig.baseUrl,
    connectTimeout: const Duration(seconds: 15),
    receiveTimeout: const Duration(seconds: 30),
  ));

  // 사진 업로드 -> 음식 TOP3 예측
  // 반환: {predictions, image_id, need_manual_input}
  Future<({List<Prediction> preds, String imageId, bool needManual})> predict(
      String imagePath) async {
    final form = FormData.fromMap({
      'image': await MultipartFile.fromFile(imagePath),
    });
    final res = await _dio.post('/api/predict', data: form);
    final data = res.data['data'];
    final preds = (data['predictions'] as List)
        .map((e) => Prediction.fromJson(e))
        .toList();
    return (
      preds: preds,
      imageId: data['image_id'].toString(),
      needManual: data['need_manual_input'] == true,
    );
  }

  // 메뉴 검색 (결과수정 화면의 드롭다운용)
  Future<List<Prediction>> searchFoods(String query) async {
    final res = await _dio.post('/api/foods/search', data: {'query': query});
    final List list = res.data['data'];
    return list
        .map((e) => Prediction(
              label: e['name_ko'].toString(),
              confidence: 1.0,
              kcal: (e['kcal_per_serving'] as num).toInt(),
            ))
        .toList();
  }

  // 식단 저장
  Future<void> createLog({
    required String date,
    required String mealType,
    required String foodName,
    required int kcal,
    String? imagePath,
    String? memo,
  }) async {
    await _dio.post('/api/logs', data: {
      'date': date,
      'meal_type': mealType,
      'food_name': foodName,
      'kcal': kcal,
      if (imagePath != null) 'image_path': imagePath,
      if (memo != null) 'memo': memo,
    });
  }

  // 일별 조회 -> (리스트, 총kcal)
  Future<({List<DietLog> items, int totalKcal})> getLogs(String date) async {
    final res = await _dio.get('/api/logs', queryParameters: {'date': date});
    final data = res.data['data'];
    final items =
        (data['items'] as List).map((e) => DietLog.fromJson(e)).toList();
    return (items: items, totalKcal: (data['total_kcal'] as num).toInt());
  }

  // 기록 삭제
  Future<void> deleteLog(int id) async {
    await _dio.delete('/api/logs/$id');
  }

  // 월별 캘린더: {날짜: 총kcal}
  Future<Map<String, int>> getCalendar(int year, int month) async {
    final res = await _dio.get('/api/calendar',
        queryParameters: {'year': year, 'month': month});
    final List days = res.data['data']['days'];
    return {for (var d in days) d['date'].toString(): (d['total_kcal'] as num).toInt()};
  }
}
