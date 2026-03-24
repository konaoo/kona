import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tool/pages/news_page.dart';

void main() {
  testWidgets('NewsPage delayed loader does not call setState after dispose', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1080, 1920);
    tester.view.devicePixelRatio = 3.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    Future<Map<String, dynamic>> delayedLoader({
      required int page,
      required int pageSize,
    }) async {
      await Future<void>.delayed(const Duration(milliseconds: 80));
      return <String, dynamic>{
        'items': <Map<String, dynamic>>[],
        'page': page,
        'page_size': pageSize,
        'has_more': false,
      };
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: NewsPage(newsLoader: delayedLoader)),
      ),
    );

    await tester.pump(const Duration(milliseconds: 10));
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump(const Duration(milliseconds: 120));

    expect(tester.takeException(), isNull);
  });
}
