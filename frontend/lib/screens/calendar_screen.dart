import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:table_calendar/table_calendar.dart';
import '../models/diet.dart';
import '../services/api.dart';

// 3번 화면: 월 캘린더 + 날짜별 리스트/총kcal + 삭제
class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});
  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  final _api = ApiService();
  DateTime _focused = DateTime.now();
  DateTime _selected = DateTime.now();
  Map<String, int> _monthKcal = {}; // 날짜 -> 총kcal
  List<DietLog> _items = [];
  int _total = 0;
  bool _loading = false;

  String get _selKey => DateFormat('yyyy-MM-dd').format(_selected);

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    setState(() => _loading = true);
    try {
      final m = await _api.getCalendar(_focused.year, _focused.month);
      final d = await _api.getLogs(_selKey);
      setState(() {
        _monthKcal = m;
        _items = d.items;
        _total = d.totalKcal;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('불러오기 실패: $e')));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('내 식단 캘린더')),
      body: Column(
        children: [
          TableCalendar(
            firstDay: DateTime(2024, 1, 1),
            lastDay: DateTime(2030, 12, 31),
            focusedDay: _focused,
            selectedDayPredicate: (d) => isSameDay(d, _selected),
            onDaySelected: (sel, foc) {
              setState(() {
                _selected = sel;
                _focused = foc;
              });
              _reload();
            },
            onPageChanged: (foc) {
              _focused = foc;
              _reload();
            },
            // 날짜 아래에 kcal 표시
            calendarBuilders: CalendarBuilders(
              markerBuilder: (context, day, events) {
                final k = _monthKcal[DateFormat('yyyy-MM-dd').format(day)] ?? 0;
                if (k == 0) return null;
                return Text('$k', style: const TextStyle(fontSize: 10, color: Colors.green));
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Text('$_selKey  총 $_total kcal (${_items.length}건)',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _items.isEmpty
                    ? const Center(child: Text('기록이 없어요. 홈에서 촬영하세요!'))
                    : ListView.builder(
                        itemCount: _items.length,
                        itemBuilder: (_, i) {
                          final it = _items[i];
                          return ListTile(
                            title: Text('${it.mealType} · ${it.foodName}'),
                            subtitle: Text(it.memo ?? ''),
                            trailing: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text('${it.kcal}kcal'),
                                IconButton(
                                  icon: const Icon(Icons.delete, color: Colors.red),
                                  onPressed: () async {
                                    await _api.deleteLog(it.id);
                                    _reload();
                                  },
                                ),
                              ],
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
