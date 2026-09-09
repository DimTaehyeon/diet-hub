import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import '../services/api.dart';
import 'result_screen.dart';

// 1번 화면: 카메라 촬영 -> /api/predict 호출 -> 결과 화면으로 이동
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _api = ApiService();
  bool _loading = false;
  String? _error;

  // 식사 타입 선택 (기본 점심)
  String _mealType = '점심';
  final _meals = ['아침', '점심', '저녁', '간식'];

  Future<void> _takePhoto() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      // 카메라로 촬영 (에뮬레이터면 갤러리에서 선택해도 됨)
      final XFile? file =
          await ImagePicker().pickImage(source: ImageSource.camera);
      if (file == null) {
        setState(() => _loading = false);
        return; // 사용자가 취소
      }
      // 서버에 전송 후 결과 화면으로 이동
      final r = await _api.predict(file.path);
      if (!mounted) return;
      Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => ResultScreen(
          imagePath: file.path,
          predictions: r.preds,
          needManual: r.needManual,
          defaultMealType: _mealType,
        ),
      ));
    } catch (e) {
      setState(() => _error = '예측 실패: $e\n(백엔드 실행 + baseUrl 확인)');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final today = DateFormat('yyyy-MM-dd').format(DateTime.now());
    return Scaffold(
      appBar: AppBar(title: Text('오늘 뭐 먹었어? ($today)')),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 식사 타입 선택
            const Text('식사 구분'),
            DropdownButton<String>(
              value: _mealType,
              items: _meals
                  .map((m) => DropdownMenuItem(value: m, child: Text(m)))
                  .toList(),
              onChanged: (v) => setState(() => _mealType = v!),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _loading ? null : _takePhoto,
              icon: const Icon(Icons.camera_alt),
              label: Text(_loading ? 'AI 분석 중...' : '카메라로 음식 찍기'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 16),
              Text(_error!, style: const TextStyle(color: Colors.red)),
            ],
            const SizedBox(height: 16),
            const Text(
              '팁: 백엔드가 켜져 있어야 합니다.\n'
              '안드로이드 에뮬레이터 → http://10.0.2.2:8000\n'
              '실기기 → PC LAN IP로 변경 (config.dart)',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}
