import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/chat_message.dart';
import 'package:tool/services/ai_chat_history_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
  });

  test('AiChatHistoryService persists and restores messages by user', () async {
    final service = AiChatHistoryService();
    final messages = <ChatMessage>[
      ChatMessage(
        role: 'user',
        content: '你好',
        timestamp: DateTime.parse('2026-03-19T12:00:00Z'),
      ),
      ChatMessage(
        role: 'assistant',
        content: '你好，我是小咔',
        timestamp: DateTime.parse('2026-03-19T12:00:05Z'),
      ),
    ];

    await service.persistMessages(
      userId: 'user-1',
      username: 'kona',
      messages: messages,
    );

    final restored = await service.loadMessages(
      userId: 'user-1',
      username: 'kona',
    );

    expect(restored.length, 2);
    expect(restored[0].role, 'user');
    expect(restored[0].content, '你好');
    expect(restored[1].role, 'assistant');
    expect(restored[1].content, '你好，我是小咔');
  });

  test('AiChatHistoryService separates history by user', () async {
    final service = AiChatHistoryService();

    await service.persistMessages(
      userId: 'user-a',
      username: 'kona',
      messages: [ChatMessage(role: 'user', content: 'A')],
    );
    await service.persistMessages(
      userId: 'user-b',
      username: 'other',
      messages: [ChatMessage(role: 'user', content: 'B')],
    );

    final a = await service.loadMessages(userId: 'user-a', username: 'kona');
    final b = await service.loadMessages(userId: 'user-b', username: 'other');

    expect(a.single.content, 'A');
    expect(b.single.content, 'B');
  });
}
