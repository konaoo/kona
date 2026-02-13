import 'package:flutter_test/flutter_test.dart';
import 'package:tool/widgets/fab_scroll_visibility_controller.dart';

void main() {
  test('小幅上划不隐藏，超过阈值后隐藏且仅一次', () {
    final controller = FabScrollVisibilityController(minToggleIntervalMs: 0);
    expect(controller.onScrollUpdate(10), isNull);
    expect(controller.onScrollUpdate(13), isNull); // 累计 23
    expect(controller.onScrollUpdate(1), isFalse); // 累计 24，触发隐藏
    expect(controller.onScrollUpdate(40), isNull); // 已隐藏，不重复触发
  });

  test('小幅下划不显示，超过阈值后显示', () {
    final controller = FabScrollVisibilityController(minToggleIntervalMs: 0);
    expect(controller.onScrollUpdate(24), isFalse); // 先隐藏
    expect(controller.onScrollUpdate(-10), isNull);
    expect(controller.onScrollUpdate(-5), isNull); // 累计 15
    expect(controller.onScrollUpdate(-1), isTrue); // 累计 16，触发显示
  });

  test('idle 只重置累计，不直接切换可见性', () {
    final controller = FabScrollVisibilityController(minToggleIntervalMs: 0);
    expect(controller.onScrollUpdate(24), isFalse); // 隐藏
    expect(controller.onScrollUpdate(-10), isNull); // 还没到显示阈值
    controller.onScrollIdle();
    expect(controller.onScrollUpdate(-10), isNull); // idle 后重新累计
  });

  test('方向抖动不会连续 toggle', () {
    final controller = FabScrollVisibilityController(minToggleIntervalMs: 0);
    expect(controller.onScrollUpdate(24), isFalse); // 隐藏
    expect(controller.onScrollUpdate(-8), isNull);
    expect(controller.onScrollUpdate(4), isNull); // 方向反转，down 累计被清掉
    expect(controller.onScrollUpdate(-8), isNull); // 累计仅 8，不会显示
  });

  test('最小切换间隔内忽略切换请求', () async {
    final controller = FabScrollVisibilityController(minToggleIntervalMs: 180);
    expect(controller.onScrollUpdate(24), isFalse); // 隐藏
    expect(controller.onScrollUpdate(-20), isNull); // 间隔未到，忽略
    await Future<void>.delayed(const Duration(milliseconds: 190));
    expect(controller.onScrollUpdate(-20), isTrue); // 间隔后允许显示
  });
}
