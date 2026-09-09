// 백엔드 {success, data, error} 응답에 맞는 모델
class Prediction {
  final String label;
  final double confidence;
  final int kcal;

  Prediction({required this.label, required this.confidence, required this.kcal});

  factory Prediction.fromJson(Map<String, dynamic> j) => Prediction(
        label: (j['label'] ?? '').toString(),
        confidence: (j['confidence'] as num? ?? 0).toDouble(),
        kcal: (j['kcal'] as num? ?? 0).toInt(),
      );
}

class DietLog {
  final int id;
  final String date; // YYYY-MM-DD
  final String mealType;
  final String foodName;
  final int kcal;
  final String? memo;

  DietLog({
    required this.id,
    required this.date,
    required this.mealType,
    required this.foodName,
    required this.kcal,
    this.memo,
  });

  factory DietLog.fromJson(Map<String, dynamic> j) => DietLog(
        id: (j['id'] as num).toInt(),
        date: j['date'].toString(),
        mealType: j['meal_type'].toString(),
        foodName: j['food_name'].toString(),
        kcal: (j['kcal'] as num).toInt(),
        memo: j['memo']?.toString(),
      );
}
