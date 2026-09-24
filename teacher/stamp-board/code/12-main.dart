import 'package:flutter/material.dart';

const stampGoal = 5;

void main() {
  runApp(const StampApp());
}

class StampApp extends StatelessWidget {
  const StampApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'スタンプ帳',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF287A70)),
        scaffoldBackgroundColor: const Color(0xFFF6F7F2),
      ),
      home: const StampBoardPage(),
    );
  }
}

class Habit {
  Habit({required this.name, required this.reason, this.count = 0});

  final String name;
  final String reason;
  int count;
}

class StampBoardPage extends StatefulWidget {
  const StampBoardPage({super.key});

  @override
  State<StampBoardPage> createState() => _StampBoardPageState();
}

class _StampBoardPageState extends State<StampBoardPage> {
  final List<Habit> habits = [
    Habit(name: 'コードを15分読む', reason: '気になったアプリの仕組みを、少しずつ読めるようになりたい。'),
    Habit(name: '外を10分歩く', reason: '画面から離れて気分を切り替え、次の作業を気持ちよく始めたい。'),
    Habit(name: '学びを1行メモ', reason: '今日分かったことを自分の言葉にして、明日の自分へ残したい。'),
  ];

  void changeStamp(Habit habit, int change) {
    final nextCount = habit.count + change;
    if (nextCount < 0 || nextCount > stampGoal) {
      return;
    }
    setState(() {
      habit.count = nextCount;
    });
  }

  @override
  Widget build(BuildContext context) {
    var total = 0;
    for (final habit in habits) {
      total += habit.count;
    }
    return Scaffold(
      appBar: AppBar(title: const Text('スタンプ帳')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const Text(
              '小さな「できた」を、\nひとつずつ。',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text('できたときに1つ押そう。まずは各$stampGoal回。'),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFFDDEFE7),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                children: [
                  const Icon(Icons.auto_awesome, size: 32),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Text(
                      '集めたスタンプ  $total 個',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            for (final habit in habits) buildHabitCard(habit),
            const SizedBox(height: 8),
            const Text('この段階ではアプリを終了すると回数は0に戻ります。'),
          ],
        ),
      ),
    );
  }

  Widget buildHabitCard(Habit habit) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              habit.name,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            StampMarks(count: habit.count),
            const SizedBox(height: 8),
            Text(
              habit.count == stampGoal
                  ? '$stampGoal回達成！ 小さな積み重ねができました。'
                  : '${habit.count} / $stampGoal 回 · あと${stampGoal - habit.count}回',
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                FilledButton.icon(
                  onPressed: habit.count < stampGoal
                      ? () => changeStamp(habit, 1)
                      : null,
                  icon: const Icon(Icons.add),
                  label: const Text('スタンプを押す'),
                ),
                TextButton(
                  onPressed: habit.count > 0
                      ? () => changeStamp(habit, -1)
                      : null,
                  child: const Text('1つ戻す'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class StampMarks extends StatelessWidget {
  const StampMarks({super.key, required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (var i = 0; i < stampGoal; i++)
          Icon(
            i < count ? Icons.check_circle : Icons.radio_button_unchecked,
            color: i < count
                ? const Color(0xFF287A70)
                : const Color(0xFF89958F),
            size: 36,
          ),
      ],
    );
  }
}
