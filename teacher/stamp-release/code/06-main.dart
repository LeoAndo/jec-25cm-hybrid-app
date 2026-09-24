import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

const stampGoal = 5;
const storageKey = 'jec-25cm-stamp-release-v1';

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
  final preferences = SharedPreferencesAsync();
  List<Habit> habits = [];
  bool isLoading = false;
  bool isSaving = false;
  bool canSave = true;
  String message = '';

  @override
  void initState() {
    super.initState();
    habits = createInitialHabits();
    message = '保存はできますが、このSTEPではまだ読み込みません。';
  }

  List<Habit> createInitialHabits() {
    return [
      Habit(name: 'コードを15分読む', reason: '気になったアプリの仕組みを、少しずつ読めるようになりたい。'),
      Habit(name: '外を10分歩く', reason: '画面から離れて気分を切り替え、次の作業を気持ちよく始めたい。'),
      Habit(name: '学びを1行メモ', reason: '今日分かったことを自分の言葉にして、明日の自分へ残したい。'),
    ];
  }

  Future<bool> saveHabits(List<Habit> nextHabits) async {
    if (isLoading || isSaving || !canSave) return false;
    setState(() {
      isSaving = true;
      message = '保存中です。';
    });
    try {
      // 名前・理由・回数の順を、読む側のdecodeHabitsとそろえる。
      final values = <String>[];
      for (final habit in nextHabits) {
        values.add(habit.name);
        values.add(habit.reason);
        values.add(habit.count.toString());
      }
      await preferences.setStringList(storageKey, values);
      if (!mounted) return false;
      setState(() {
        habits = nextHabits;
        message = 'この端末に保存しました。';
      });
      return true;
    } catch (error) {
      if (mounted) {
        setState(() {
          message = '保存できませんでした。内容を変えずに残しています。もう一度試してください。';
        });
      }
      return false;
    } finally {
      if (mounted) {
        setState(() {
          isSaving = false;
        });
      }
    }
  }

  Future<void> changeStamp(Habit habit, int change) async {
    if (isLoading || isSaving || !canSave) return;
    final nextCount = habit.count + change;
    if (nextCount < 0 || nextCount > stampGoal) return;
    // 保存に成功するまで、表示中のHabitを直接変更しない。
    final nextHabits = <Habit>[];
    for (final item in habits) {
      nextHabits.add(
        Habit(
          name: item.name,
          reason: item.reason,
          count: item == habit ? nextCount : item.count,
        ),
      );
    }
    await saveHabits(nextHabits);
  }

  Future<bool> addHabit(Habit habit) async {
    final nextHabits = List<Habit>.of(habits);
    nextHabits.add(habit);
    return await saveHabits(nextHabits);
  }

  void openAdd() {
    Navigator.push(
      context,
      MaterialPageRoute<void>(
        builder: (context) => AddHabitPage(onSave: addHabit),
      ),
    );
  }

  void openDetail(Habit habit) {
    Navigator.push(
      context,
      MaterialPageRoute<void>(
        builder: (context) => HabitDetailPage(habit: habit),
      ),
    );
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
            if (isLoading || isSaving) const LinearProgressIndicator(),
            const SizedBox(height: 8),
            Text(message),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: !canSave || isLoading || isSaving ? null : openAdd,
              icon: const Icon(Icons.add),
              label: const Text('習慣を追加'),
            ),
            const SizedBox(height: 20),
            if (canSave && habits.isEmpty)
              const Text('習慣はまだありません。「習慣を追加」から始めましょう。'),
            for (final habit in habits) buildHabitCard(habit),
            const SizedBox(height: 8),
            const Text('記録はこの端末だけに残ります。提出するAPKに入力済みデータは含まれません。'),
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
                  onPressed:
                      canSave &&
                          !isLoading &&
                          !isSaving &&
                          habit.count < stampGoal
                      ? () => changeStamp(habit, 1)
                      : null,
                  icon: const Icon(Icons.add),
                  label: const Text('スタンプを押す'),
                ),
                TextButton(
                  onPressed:
                      canSave && !isLoading && !isSaving && habit.count > 0
                      ? () => changeStamp(habit, -1)
                      : null,
                  child: const Text('1つ戻す'),
                ),
                TextButton(
                  onPressed: isLoading || isSaving
                      ? null
                      : () => openDetail(habit),
                  child: const Text('詳しく見る'),
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

class HabitDetailPage extends StatelessWidget {
  const HabitDetailPage({super.key, required this.habit});

  final Habit habit;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('習慣の詳細')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Text(
              habit.name,
              style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            StampMarks(count: habit.count),
            const SizedBox(height: 12),
            Text('${habit.count} / $stampGoal 回'),
            const SizedBox(height: 32),
            const Text(
              '続けたい理由',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              habit.reason,
              style: const TextStyle(fontSize: 17, height: 1.7),
            ),
            const SizedBox(height: 32),
            const Text('スタンプは一覧画面で押せます。できたタイミングは自分で決めましょう。'),
          ],
        ),
      ),
    );
  }
}

class AddHabitPage extends StatefulWidget {
  const AddHabitPage({super.key, required this.onSave});

  final Future<bool> Function(Habit) onSave;

  @override
  State<AddHabitPage> createState() => _AddHabitPageState();
}

class _AddHabitPageState extends State<AddHabitPage> {
  final nameController = TextEditingController();
  final reasonController = TextEditingController();
  bool isSaving = false;
  String message = '';

  @override
  void dispose() {
    nameController.dispose();
    reasonController.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (isSaving) return;
    final name = nameController.text.trim();
    final reason = reasonController.text.trim();
    if (name.isEmpty || reason.isEmpty) {
      setState(() {
        message = '習慣の名前と、続けたい理由を入力してください。';
      });
      return;
    }
    setState(() {
      isSaving = true;
      message = '保存中です。';
    });
    final saved = await widget.onSave(Habit(name: name, reason: reason));
    if (!mounted) return;
    if (saved) {
      Navigator.pop(context);
    } else {
      setState(() {
        isSaving = false;
        message = '保存できませんでした。入力は残っています。もう一度試してください。';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: !isSaving,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('習慣を追加'),
          leading: IconButton(
            onPressed: isSaving ? null : () => Navigator.pop(context),
            icon: const Icon(Icons.arrow_back),
            tooltip: '戻る',
          ),
        ),
        body: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const Text(
                '小さく始められる習慣を、\nひとつ。',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: nameController,
                enabled: !isSaving,
                maxLength: 40,
                decoration: const InputDecoration(
                  labelText: '習慣の名前',
                  hintText: '例：サンプルを10分動かす',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: reasonController,
                enabled: !isSaving,
                maxLength: 200,
                minLines: 3,
                maxLines: 5,
                decoration: const InputDecoration(
                  labelText: '続けたい理由',
                  hintText: '自分がうれしいと思う変化を書こう',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              Text(message),
              if (isSaving) const LinearProgressIndicator(),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: isSaving ? null : submit,
                child: const Text('追加して保存'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
