// API 주소 설정
// - 안드로이드 에뮬레이터: http://10.0.2.2:8000 (기본값)
// - iOS 시뮬레이터/PC 크롬: --dart-define=API_BASE=http://127.0.0.1:8000 로 실행
// - 실기기: PC의 LAN IP로 변경 (예: http://192.168.0.5:8000)
class AppConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE',
    defaultValue: 'http://10.0.2.2:8000',
  );
}
