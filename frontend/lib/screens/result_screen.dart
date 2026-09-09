import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/diet.dart';
import '../services/api.dart';

// 2번 화면: AI TOP3 표시 + 수정/인분수 조절 -> 저장
class ResultScreen extends StatefulWidget {
  final String imagePath;
  final List<Prediction> predictions;
  final bool needManual;
  final String defaultMealType;

  const ResultScreen({
    super.key,
    required this.imagePath,
    required this.predictions,
    required this.needManual,
    required this.defaultMealType,
  });

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  final _api = ApiService();
  late String _foodName;
  late int _kcalPerServing;
  double _serving = 1.0; // 0.5 / 1 / 1.5 / 2
  late String _mealType;
  final _searchCtrl = TextEditingController();
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    // TOP1을 기본 선택 (없으면 직접입력)
    if (widget.predictions.isNotEmpty &&
        widget.predictions.first.label != '직접입력 필요') {
      _foodName = widget.predictions.first.label;
      _kcalPerServing = widget.predictions.first.kcal;
    } else {
      _foodName = '';
      _kcalPerServing = 0;
    }
    _mealType = widget.defaultMealType;
  }

  int get _totalKcal => (_kcalPerServing * _serving).round();

  // 예측 후보를 탭하면 선택
  void _pick(Prediction p) {
    setState(() {
      _foodName = p.label;
      _kcalPerServing = p.kcal;
    });
  }

  // 메뉴 직접 검색 (AI가 틀렸을 때)
  Future<void> _search() async {
    final q = _searchCtrl.text.trim();
    if (q.isEmpty) return;
    final list = await _api.searchFoods(q);
    if (!mounted) return;
    showDialog(
      context: context,
      builder: (_) => SimpleDialog(
        title: Text('"$q" 검색 결과'),
        children: list
            .map((p) => SimpleDialogOption(
                  onPressed: () {
                    _pick(p);
                    Navigator.pop(context);
                  },
                  child: Text('${p.label} (${p.kcal}kcal)'),
                ))
            .toList(),
      ),
    );
  }

  Future<void> _save() async {
    if (_foodName.isEmpty) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('메뉴를 선택/입력하세요')));
      return;
    }
    setState(() => _saving = true);
    try {
      await _api.createLog(
        date: DateFormat('yyyy-MM-dd').format(DateTime.now()),
        mealType: _mealType,
        foodName: _foodName,
        kcal: _totalKcal,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('$_foodName $_totalKcal kcal 저장됨')));
      Navigator.of(context).popUntil((r) => r.isFirst);
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('저장 실패: $e')));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('분석 결과 확인')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (widget.needManual)
            const Card(
              color: Color(0xFFFFF3E0),
              child: Padding(
                padding: EdgeInsets.all(12),
                child: Text('AI 확신이 낮아요. 아래에서 직접 메뉴를 골라주세요.'),
              ),
            ),
          const Text('AI 예측 TOP3', style: TextStyle(fontWeight: FontWeight.bold)),
          ...widget.predictions.map((p) => ListTile(
                title: Text('${p.label} (${(p.confidence * 100).toStringAsFixed(1)}%)'),
                subtitle: Text('${p.kcal} kcal / 1인분'),
                trailing: _foodName == p.label
                    ? const Icon(Icons.check_circle, color: Colors.green)
                    : null,
                onTap: () => _pick(p),
              )),
          const Divider(),
          // 직접 검색
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _searchCtrl,
                  decoration: const InputDecoration(
                      labelText: '메뉴 직접 검색 (예: 김치찌개)', border: OutlineInputBorder()),
                ),
              ),
              IconButton(onPressed: _search, icon: const Icon(Icons.search)),
            ],
          ),
          const SizedBox(height: 12),
          // 선택된 메뉴 표시
          Text('선택: $_foodName ($_kcalPerServing kcal/1인분)',
              style: const TextStyle(fontSize: 16)),
          const SizedBox(height: 8),
          // 인분수 조절
          Row(
            children: [0.5, 1.0, 1.5, 2.0]
                .map((s) => ChoiceChip(
                      label: Text('$s인분'),
                      selected: _serving == s,
                      onSelected: (_) => setState(() => _serving = s),
                    ))
                .toList(),
          ),
          const SizedBox(height: 8),
          Text('총 칼로리: $_totalKcal kcal',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          DropdownButton<String>(
            value: _mealType,
            items: ['아침', '점심', '저녁', '간식']
                .map((m) => DropdownMenuItem(value: m, child: Text(m)))
                .toList(),
            onChanged: (v) => setState(() => _mealType = v!),
          ),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: _saving ? null : _save,
            child: Text(_saving ? '저장 중...' : '캘린더에 저장'),
          ),
        ],
      ),
    );
  }
}
