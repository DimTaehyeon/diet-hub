import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'screens/calendar_screen.dart';

// 앱 진입점: 하단 탭 2개 (홈=카메라, 캘린더)
void main() {
  runApp(const DietApp());
}

class DietApp extends StatelessWidget {
  const DietApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '식단 관리',
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.green),
      home: const MainTabs(),
    );
  }
}

class MainTabs extends StatefulWidget {
  const MainTabs({super.key});
  @override
  State<MainTabs> createState() => _MainTabsState();
}

class _MainTabsState extends State<MainTabs> {
  int _idx = 0;
  final _pages = const [HomeScreen(), CalendarScreen()];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_idx],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _idx,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.camera_alt), label: '홈'),
          BottomNavigationBarItem(icon: Icon(Icons.calendar_month), label: '캘린더'),
        ],
        onTap: (i) => setState(() => _idx = i),
      ),
    );
  }
}
