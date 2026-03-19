import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../models/chat_message.dart';
import '../providers/app_state.dart';
import '../services/ai_chat_service.dart';
import '../services/ai_chat_history_service.dart';

/// 小咔 AI 助手聊天页
class AiChatPage extends StatefulWidget {
  const AiChatPage({super.key});

  @override
  State<AiChatPage> createState() => _AiChatPageState();
}

class _AiChatPageState extends State<AiChatPage> {
  final List<ChatMessage> _messages = [];
  final TextEditingController _inputController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final AiChatService _chatService = AiChatService();
  final AiChatHistoryService _historyService = AiChatHistoryService();
  final FocusNode _focusNode = FocusNode();

  bool _isStreaming = false;
  bool _isHydrating = true;
  VoidCallback? _cancelStream;
  int _aiCreditsBalance = 0;
  String _userGroupText = '加入咔咔用户群';
  String _userGroupImageUrl = '';

  static const _quickQuestions = [
    '帮我总结最近的资产变化',
    '分析一下我的持仓结构',
    '哪些持仓需要关注？',
    '最近收益怎么样？',
  ];

  static const _aiBadgeGradient = [
    Color(0xFF6C5CE7),
    Color(0xFF5B8DEF),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _hydratePage();
    });
  }

  @override
  void dispose() {
    _cancelStream?.call();
    _inputController.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  bool get _hasCredits => _aiCreditsBalance > 0;

  String get _creditsBadgeText => _hasCredits ? '剩余 $_aiCreditsBalance 积分' : '0 积分';

  Future<void> _hydratePage() async {
    final appState = context.read<AppState>();
    final loaded = await _historyService.loadMessages(
      userId: appState.userId,
      username: appState.username,
    );
    if (!mounted) return;
    setState(() {
      _messages
        ..clear()
        ..addAll(loaded);
      _aiCreditsBalance = appState.aiCreditsBalance;
      _isHydrating = false;
    });
    if (_messages.isNotEmpty) {
      _scrollToBottom();
    }
    unawaited(_refreshAiCreditsAndGroupConfig(appState));
  }

  Future<void> _refreshAiCreditsAndGroupConfig(AppState appState) async {
    var nextBalance = appState.aiCreditsBalance;
    var nextUserGroupText = _userGroupText;
    var nextUserGroupImageUrl = _userGroupImageUrl;

    try {
      await appState.fetchProfile();
      nextBalance = appState.aiCreditsBalance;
      if (nextBalance <= 0) {
        final config = await appState.apiService.getWebConfig();
        final resolvedText = config?['user_group_text']?.toString().trim() ?? '';
        final resolvedImageUrl =
            config?['user_group_image_url']?.toString().trim() ?? '';
        if (resolvedText.isNotEmpty) {
          nextUserGroupText = resolvedText;
        }
        nextUserGroupImageUrl = resolvedImageUrl;
      }
    } catch (_) {
      // 聊天页不因为资料或运营配置加载失败而阻断打开。
    }

    if (!mounted) return;
    setState(() {
      _aiCreditsBalance = nextBalance;
      _userGroupText = nextUserGroupText;
      _userGroupImageUrl = nextUserGroupImageUrl;
    });
  }

  void _applyCreditsRequiredState({
    required String message,
    required int aiCreditsBalance,
    required String userGroupText,
    required String userGroupImageUrl,
  }) {
    if (!mounted) return;
    setState(() {
      _isStreaming = false;
      _cancelStream = null;
      _aiCreditsBalance = aiCreditsBalance;
      if (userGroupText.trim().isNotEmpty) {
        _userGroupText = userGroupText.trim();
      }
      _userGroupImageUrl = userGroupImageUrl.trim();
      if (_messages.isNotEmpty &&
          _messages.last.role == 'assistant' &&
          _messages.last.content.isEmpty) {
        _messages.removeLast();
      }
    });
    _persistHistory();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  Future<void> _persistHistory() async {
    if (!mounted) return;
    final appState = context.read<AppState>();
    await _historyService.persistMessages(
      userId: appState.userId,
      username: appState.username,
      messages: _messages,
    );
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage(String text) async {
    final content = text.trim();
    if (content.isEmpty || _isStreaming || !_hasCredits) return;

    _inputController.clear();
    var chargedLocally = false;

    setState(() {
      _messages.add(ChatMessage(role: 'user', content: content));
      _messages.add(ChatMessage(role: 'assistant', content: ''));
      _isStreaming = true;
    });
    await _persistHistory();
    _scrollToBottom();

    _cancelStream = await _chatService.sendMessage(
      messages: _messages.where((m) => m.content.isNotEmpty).toList(),
      onDelta: (delta) {
        setState(() {
          if (!chargedLocally) {
            _aiCreditsBalance = (_aiCreditsBalance - 1).clamp(0, 1 << 30).toInt();
            chargedLocally = true;
          }
          final last = _messages.last;
          _messages[_messages.length - 1] = ChatMessage(
            role: 'assistant',
            content: last.content + delta,
            timestamp: last.timestamp,
          );
        });
        _persistHistory();
        _scrollToBottom();
      },
      onDone: () {
        setState(() {
          _isStreaming = false;
          _cancelStream = null;
          // 如果 assistant 消息为空则移除
          if (_messages.isNotEmpty && _messages.last.content.isEmpty) {
            _messages.removeLast();
          }
        });
        _persistHistory();
      },
      onError: (error) {
        setState(() {
          _isStreaming = false;
          _cancelStream = null;
          // 替换空的 assistant 消息为错误提示
          if (_messages.isNotEmpty && _messages.last.role == 'assistant') {
            _messages[_messages.length - 1] = ChatMessage(
              role: 'assistant',
              content: '⚠️ $error',
            );
          }
        });
        _persistHistory();
      },
      onCreditsRequired: ({
        required String message,
        required int aiCreditsBalance,
        required String userGroupText,
        required String userGroupImageUrl,
      }) {
        _applyCreditsRequiredState(
          message: message,
          aiCreditsBalance: aiCreditsBalance,
          userGroupText: userGroupText,
          userGroupImageUrl: userGroupImageUrl,
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      appBar: AppBar(
        backgroundColor: AppTheme.bgCard,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(
            Icons.arrow_back_ios_new,
            size: 18,
            color: AppTheme.textPrimary,
          ),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 26,
              height: 26,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                gradient: const LinearGradient(
                  colors: [Color(0xFF6C5CE7), Color(0xFF5B8DEF)],
                ),
              ),
              child: const Icon(
                Icons.auto_awesome,
                size: 14,
                color: Colors.white,
              ),
            ),
            const SizedBox(width: 8),
            Text(
              '小咔助手',
              style: GoogleFonts.dmSans(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
          ],
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 14),
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: AppTheme.surface2,
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(color: AppTheme.borderSubtle, width: 0.5),
                ),
                child: Text(
                  _creditsBadgeText,
                  style: GoogleFonts.dmSans(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textSecondary,
                  ),
                ),
              ),
            ),
          ),
        ],
        centerTitle: true,
      ),
      body: SafeArea(
        child: Column(
          children: [
            // 消息列表
            Expanded(
              child: _isHydrating
                  ? _buildLoadingState()
                  : (_messages.isEmpty
                        ? (_hasCredits ? _buildWelcome() : _buildNoCreditsState())
                        : _buildConversation()),
            ),
            // 输入栏
            _buildInputBar(),
          ],
        ),
      ),
    );
  }

  Widget _buildConversation() {
    return Column(
      children: [
        if (!_hasCredits) _buildNoCreditsBanner(),
        Expanded(child: _buildMessageList()),
      ],
    );
  }

  Widget _buildWelcome() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          const SizedBox(height: 40),
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(20),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF6C5CE7), Color(0xFF5B8DEF)],
              ),
            ),
            child: const Icon(
              Icons.auto_awesome,
              size: 32,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            '你好，我是小咔',
            style: GoogleFonts.dmSans(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: AppTheme.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '你的 AI 投资助手，可以帮你分析持仓、解读趋势',
            style: GoogleFonts.dmSans(
              fontSize: 13,
              color: AppTheme.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),
          // 预设快捷问题
          ...List.generate(_quickQuestions.length, (i) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: _isStreaming
                      || !_hasCredits
                      ? null
                      : () => _sendMessage(_quickQuestions[i]),
                  style: OutlinedButton.styleFrom(
                    side: BorderSide(color: AppTheme.border),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 14,
                    ),
                    backgroundColor: AppTheme.bgCard,
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.chat_bubble_outline,
                        size: 16,
                        color: AppTheme.accent,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _quickQuestions[i],
                          style: GoogleFonts.dmSans(
                            fontSize: 14,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ),
                      Icon(
                        Icons.arrow_forward_ios,
                        size: 12,
                        color: AppTheme.textTertiary,
                      ),
                    ],
                  ),
                ),
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 22,
            height: 22,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation(AppTheme.accent),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            '正在恢复聊天记录…',
            style: GoogleFonts.dmSans(
              fontSize: 13,
              color: AppTheme.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNoCreditsState() {
    return LayoutBuilder(
      builder: (context, constraints) {
        return SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 28, 20, 24),
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight - 8),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 360),
                child: _buildNoCreditsBanner(isFullPage: true),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildAiBadgeIcon({
    required IconData icon,
    double size = 72,
    double iconSize = 32,
  }) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(size * 0.32),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: _aiBadgeGradient,
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF6C5CE7).withValues(alpha: 0.28),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Icon(icon, size: iconSize, color: Colors.white),
    );
  }

  Widget _buildCreditRuleCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: AppTheme.surface2,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.borderSubtle, width: 0.5),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(Icons.stars_rounded, size: 16, color: AppTheme.accentLight),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '当前剩余：$_aiCreditsBalance 积分',
                  style: GoogleFonts.dmSans(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.textPrimary,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Icon(
                Icons.bolt_rounded,
                size: 16,
                color: AppTheme.gold,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '消耗规则：每次成功对话消耗 1 积分',
                  style: GoogleFonts.dmSans(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.textPrimary,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildNoCreditsBanner({bool isFullPage = false}) {
    return Container(
      margin: isFullPage ? EdgeInsets.zero : const EdgeInsets.fromLTRB(16, 16, 16, 12),
      padding: const EdgeInsets.fromLTRB(20, 22, 20, 20),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppTheme.borderSubtle, width: 0.5),
        boxShadow: AppTheme.cardShadow,
      ),
      child: Column(
        children: [
          _buildAiBadgeIcon(
            icon: Icons.lock_outline_rounded,
            size: 60,
            iconSize: 26,
          ),
          const SizedBox(height: 18),
          Text(
            '当前积分不足',
            style: GoogleFonts.dmSans(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: AppTheme.textPrimary,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            '小咔助手暂时无法继续提问',
            textAlign: TextAlign.center,
            style: GoogleFonts.dmSans(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppTheme.textSecondary,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 18),
          _buildCreditRuleCard(),
          if (_userGroupImageUrl.isNotEmpty) ...[
            const SizedBox(height: 22),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppTheme.surface2,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppTheme.borderSubtle, width: 0.5),
              ),
              child: Column(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(18),
                    child: Image.network(
                      _userGroupImageUrl,
                      width: 230,
                      height: 230,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) {
                        return Container(
                          width: 230,
                          height: 230,
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(18),
                          ),
                          child: const Icon(
                            Icons.qr_code_2,
                            size: 96,
                            color: Colors.black,
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 14),
                  Text(
                    '扫码加入用户群',
                    textAlign: TextAlign.center,
                    style: GoogleFonts.dmSans(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMessageList() {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      itemCount: _messages.length,
      itemBuilder: (context, index) {
        final msg = _messages[index];
        return _buildMessageBubble(msg, index);
      },
    );
  }

  Widget _buildMessageBubble(ChatMessage msg, int index) {
    final isUser = msg.role == 'user';
    final isLastAssistant =
        !isUser && index == _messages.length - 1 && _isStreaming;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: isUser
            ? MainAxisAlignment.end
            : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              width: 28,
              height: 28,
              margin: const EdgeInsets.only(top: 2),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                gradient: const LinearGradient(
                  colors: [Color(0xFF6C5CE7), Color(0xFF5B8DEF)],
                ),
              ),
              child: const Icon(
                Icons.auto_awesome,
                size: 14,
                color: Colors.white,
              ),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: isUser
                    ? AppTheme.accent.withValues(alpha: 0.15)
                    : AppTheme.bgCard,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(isUser ? 16 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 16),
                ),
                border: isUser
                    ? null
                    : Border.all(color: AppTheme.borderSubtle, width: 0.5),
              ),
              child: isUser
                  ? Text(
                      msg.content,
                      style: GoogleFonts.dmSans(
                        fontSize: 14,
                        color: AppTheme.textPrimary,
                        height: 1.5,
                      ),
                    )
                  : msg.content.isEmpty && isLastAssistant
                  ? _buildTypingIndicator()
                  : _buildMarkdownBody(msg.content),
            ),
          ),
          if (isUser) const SizedBox(width: 8),
        ],
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: 16,
          height: 16,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation(AppTheme.accent),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          '思考中…',
          style: GoogleFonts.dmSans(
            fontSize: 13,
            color: AppTheme.textSecondary,
          ),
        ),
      ],
    );
  }

  Widget _buildMarkdownBody(String content) {
    return MarkdownBody(
      data: content,
      selectable: true,
      styleSheet: MarkdownStyleSheet(
        p: GoogleFonts.dmSans(
          fontSize: 14,
          color: AppTheme.textPrimary,
          height: 1.6,
        ),
        h1: GoogleFonts.dmSans(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: AppTheme.textPrimary,
        ),
        h2: GoogleFonts.dmSans(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: AppTheme.textPrimary,
        ),
        h3: GoogleFonts.dmSans(
          fontSize: 15,
          fontWeight: FontWeight.w600,
          color: AppTheme.textPrimary,
        ),
        listBullet: GoogleFonts.dmSans(
          fontSize: 14,
          color: AppTheme.textPrimary,
        ),
        code: GoogleFonts.jetBrainsMono(
          fontSize: 13,
          color: AppTheme.accent,
          backgroundColor: AppTheme.surface2,
        ),
        codeblockDecoration: BoxDecoration(
          color: AppTheme.surface2,
          borderRadius: BorderRadius.circular(8),
        ),
        blockquoteDecoration: BoxDecoration(
          border: Border(left: BorderSide(color: AppTheme.accent, width: 3)),
        ),
        tableHead: GoogleFonts.dmSans(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: AppTheme.textPrimary,
        ),
        tableBody: GoogleFonts.dmSans(
          fontSize: 13,
          color: AppTheme.textSecondary,
        ),
        tableBorder: TableBorder.all(color: AppTheme.borderSubtle, width: 0.5),
        tableCellsPadding: const EdgeInsets.symmetric(
          horizontal: 8,
          vertical: 4,
        ),
      ),
    );
  }

  Widget _buildInputBar() {
    if (!_hasCredits) {
      return const SafeArea(
        top: false,
        child: SizedBox(height: 14),
      );
    }
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        border: Border(
          top: BorderSide(color: AppTheme.borderSubtle, width: 0.5),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _inputController,
              focusNode: _focusNode,
              enabled: !_isStreaming,
              maxLines: 4,
              minLines: 1,
              textInputAction: TextInputAction.send,
              onSubmitted: _isStreaming || !_hasCredits ? null : _sendMessage,
              style: GoogleFonts.dmSans(
                fontSize: 14,
                color: AppTheme.textPrimary,
              ),
              decoration: InputDecoration(
                hintText: '问小咔一个问题…',
                hintStyle: GoogleFonts.dmSans(
                  fontSize: 14,
                  color: AppTheme.textMuted,
                ),
                filled: true,
                fillColor: AppTheme.surface2,
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 10,
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(20),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          const SizedBox(width: 6),
          _isStreaming
              ? IconButton(
                  onPressed: () {
                    _cancelStream?.call();
                    setState(() {
                      _isStreaming = false;
                      _cancelStream = null;
                    });
                  },
                  icon: Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(
                      color: AppTheme.danger,
                      borderRadius: BorderRadius.circular(17),
                    ),
                    child: const Icon(
                      Icons.stop,
                      size: 18,
                      color: Colors.white,
                    ),
                  ),
                )
              : IconButton(
                  onPressed: () => _sendMessage(_inputController.text),
                  icon: Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(
                      color: AppTheme.accent,
                      borderRadius: BorderRadius.circular(17),
                    ),
                    child: const Icon(
                      Icons.arrow_upward,
                      size: 18,
                      color: Colors.white,
                    ),
                  ),
                ),
        ],
      ),
    );
  }
}
