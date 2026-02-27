import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tool/pages/news_page.dart';

void main() {
  testWidgets('快讯页下拉刷新时保留已有列表且无中部大Loading', (tester) async {
    final refreshCompleter = Completer<void>();
    var resetCalls = 0;

    Future<Map<String, dynamic>> loader({
      required int page,
      required int pageSize,
    }) async {
      if (page != 1) {
        return <String, dynamic>{
          'items': <Map<String, dynamic>>[],
          'has_more': false,
        };
      }
      resetCalls += 1;
      if (resetCalls == 1) {
        return <String, dynamic>{
          'items': <Map<String, dynamic>>[
            <String, dynamic>{'time': '10:00', 'content': '旧快讯内容'},
          ],
          'has_more': false,
        };
      }
      await refreshCompleter.future;
      return <String, dynamic>{
        'items': <Map<String, dynamic>>[
          <String, dynamic>{'time': '10:01', 'content': '新快讯内容'},
        ],
        'has_more': false,
      };
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: NewsPage(newsLoader: loader)),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('旧快讯内容'), findsOneWidget);

    final refresh = tester.widget<RefreshIndicator>(
      find.byType(RefreshIndicator),
    );
    final refreshFuture = refresh.onRefresh();
    await tester.pump();

    expect(find.text('旧快讯内容'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    refreshCompleter.complete();
    await refreshFuture;
    await tester.pumpAndSettle();

    expect(find.text('新快讯内容'), findsOneWidget);
  });

  testWidgets('快讯页首次加载时不显示中部大Loading', (tester) async {
    final firstLoadCompleter = Completer<void>();

    Future<Map<String, dynamic>> delayedLoader({
      required int page,
      required int pageSize,
    }) async {
      await firstLoadCompleter.future;
      return <String, dynamic>{
        'items': <Map<String, dynamic>>[],
        'has_more': false,
      };
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: NewsPage(newsLoader: delayedLoader)),
      ),
    );
    await tester.pump();

    expect(find.text('市场快讯'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    firstLoadCompleter.complete();
    await tester.pumpAndSettle();
  });
}
