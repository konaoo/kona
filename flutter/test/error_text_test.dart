import 'package:flutter_test/flutter_test.dart';
import 'package:tool/utils/error_text.dart';

void main() {
  test('translateErrorText maps common English fetch errors to Chinese', () {
    expect(translateErrorText('Request failed: 500'), '服务器开小差了，请稍后重试');
    expect(translateErrorText('Failed to fetch'), '网络连接失败，请检查网络后重试');
  });

  test('resolveApiErrorText prefers code mapping and hides raw English', () {
    expect(resolveApiErrorText(code: 'INSUFFICIENT_CASH'), '账户余额不足，请更换其他账户');
    expect(
      resolveApiErrorText(code: 'AI_CREDITS_REQUIRED'),
      '当前没有可用积分，加入咔咔用户群获取积分',
    );
    expect(
      resolveApiErrorText(
        message: 'Failed to buy asset with cash',
        fallback: '保存失败，请稍后重试',
      ),
      '现金买入失败，请稍后重试',
    );
    expect(
      resolveApiErrorText(
        message: 'Some backend exception text',
        fallback: '保存失败，请稍后重试',
      ),
      '保存失败，请稍后重试',
    );
  });
}
