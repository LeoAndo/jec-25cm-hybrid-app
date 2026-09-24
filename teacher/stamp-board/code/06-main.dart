import 'package:flutter/material.dart';

void main() {
  runApp(const MainApp());
}

class MainApp extends StatelessWidget {
  const MainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        body: SafeArea(
          child: Center(
            child: Card(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('コードを15分読む', style: TextStyle(fontSize: 24)),
                    SizedBox(height: 16),
                    Icon(Icons.radio_button_unchecked, size: 36),
                    SizedBox(height: 8),
                    Text('0 / 5 回'),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
