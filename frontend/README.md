# Frontend (Flutter)

프론트 경험 없어도 3화면만 유지하면 됩니다: 홈(카메라) / 결과수정 / 캘린더

## 1. Flutter SDK 설치 (1회, PC)
- https://docs.flutter.dev/get-started/install/windows 에서 SDK 다운로드
- 압축 해제 후 `flutter --version` 확인
- `flutter doctor` 로 안드로이드 스튜디오/크롬 확인

## 2. 실행
```powershell
cd frontend
flutter pub get

# 안드로이드 에뮬레이터 (기본 baseUrl=http://10.0.2.2:8000)
flutter run

# iOS 시뮬레이터 / PC 크롬 (백엔드가 같은 PC의 8000번)
flutter run --dart-define=API_BASE=http://127.0.0.1:8000 -d chrome

# 실기기 (PC와 같은 와이파이, PC IP 확인 후)
flutter run --dart-define=API_BASE=http://192.168.0.5:8000
```

## 3. 백엔드 먼저 켜기 (필수)
```powershell
cd ..\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# 실기기 접속용으로 0.0.0.0 권장
```

## 4. 파일 설명
- `lib/main.dart` : 하단 탭 (홈/캘린더)
- `lib/config.dart` : API 주소 (API_BASE)
- `lib/services/api.dart` : predict/검색/저장/조회/삭제/캘린더
- `lib/screens/home_screen.dart` : 촬영 → 예측 → 결과로 이동
- `lib/screens/result_screen.dart` : TOP3 선택 + 직접검색 + 인분수 → 저장
- `lib/screens/calendar_screen.dart` : 월 kcal + 일별 리스트 + 삭제

## 5. 흔한 오류
- `Connection refused` → baseUrl이 PC와 다른 경우. config.dart 주석 참고
- 카메라 안 됨 (에뮬레이터) → 갤러리 선택으로 테스트하거나 실기기 사용
