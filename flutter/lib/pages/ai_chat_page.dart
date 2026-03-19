import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:google_fonts/google_fonts.dart';
import '../config/theme.dart';
import '../models/chat_message.dart';
import '../services/ai_chat_service.dart';

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
  final FocusNode _focusNode = FocusNode();

  bool _isStreaming = false;
  VoidCallback? _cancelStream;

  static const _quickQuestions = [
    '帮我总结最近的资产变化',
    '分析一下我的持仓结构',
    '哪些持仓需要关注？',
    '最近收益怎么样？',
  ];

  @override
  void dispose() {
    _cancelStream?.call();
    _inputController.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
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
    if (content.isEmpty || _isStreaming) return;

    _inputController.clear();

    setState(() {
      _messages.add(ChatMessage(role: 'user', content: content));
      _messages.add(ChatMessage(role: 'assistant', content: ''));
      _isStreaming = true;
    });
    _scrollToBottom();

    _cancelStream = await _chatService.sendMessage(
      messages: _messages.where((m) => m.content.isNotEmpty).toList(),
      onDelta: (delta) {
        setState(() {
          final last = _messages.last;
          _messages[_messages.length - 1] = ChatMessage(
            role: 'assistant',
            content: last.content + delta,
            timestamp: last.timestamp,
          );
        });
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
          icon: Icon(Icons.arrow_back_ios_new, size: 18, color: AppTheme.textPrimary),
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
              child: const Icon(Icons.auto_awesome, size: 14, color: Colors.white),
            ),
            const SizedBox(width: 8),
            Text(
              '小咔 · AI 助手',
              style: GoogleFonts.dmSans(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
          ],
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Column(
          children: [
            // 消息列表
            Expanded(
              child: _messages.isEmpty ? _buildWelcome() : _buildMessageList(),
            ),
            // 输入栏
            _buildInputBar(),
          ],
        ),
      ),
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
            child: const Icon(Icons.auto_awesome, size: 32, color: Colors.white),
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
                  onPressed: _isStreaming ? null : () => _sendMessage(_quickQuestions[i]),
                  style: OutlinedButton.styleFrom(
                    side: BorderSide(color: AppTheme.border),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    backgroundColor: AppTheme.bgCard,
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.chat_bubble_outline, size: 16, color: AppTheme.accent),
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
                      Icon(Icons.arrow_forward_ios, size: 12, color: AppTheme.textTertiary),
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
    final isLastAssistant = !isUser && index == _messages.length - 1 && _isStreaming;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
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
              child: const Icon(Icons.auto_awesome, size: 14, color: Colors.white),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: isUser ? AppTheme.accent.withValues(alpha: 0.15) : AppTheme.bgCard,
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
          style: GoogleFonts.dmSans(fontSize: 13, color: AppTheme.textSecondary),
        ),
      ],
    );
  }

  Widget _buildMarkdownBody(String content) {
    return MarkdownBody(
      data: content,
      selectable: true,
      styleSheet: MarkdownStyleSheet(
        p: GoogleFonts.dmSans(fontSize: 14, color: AppTheme.textPrimary, height: 1.6),
        h1: GoogleFonts.dmSans(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
        h2: GoogleFonts.dmSans(fontSize: 16, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
        h3: GoogleFonts.dmSans(fontSize: 15, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
        listBullet: GoogleFonts.dmSans(fontSize: 14, color: AppTheme.textPrimary),
        code: GoogleFonts.jetBrainsMono(fontSize: 13, color: AppTheme.accent, backgroundColor: AppTheme.surface2),
        codeblockDecoration: BoxDecoration(
          color: AppTheme.surface2,
          borderRadius: BorderRadius.circular(8),
        ),
        blockquoteDecoration: BoxDecoration(
          border: Border(left: BorderSide(color: AppTheme.accent, width: 3)),
        ),
        tableHead: GoogleFonts.dmSans(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
        tableBody: GoogleFonts.dmSans(fontSize: 13, color: AppTheme.textSecondary),
        tableBorder: TableBorder.all(color: AppTheme.borderSubtle, width: 0.5),
        tableCellsPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      ),
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        border: Border(top: BorderSide(color: AppTheme.borderSubtle, width: 0.5)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _inputController,
              focusNode: _focusNode,
              maxLines: 4,
              minLines: 1,
              textInputAction: TextInputAction.send,
              onSubmitted: _isStreaming ? null : _sendMessage,
              style: GoogleFonts.dmSans(fontSize: 14, color: AppTheme.textPrimary),
              decoration: InputDecoration(
                hintText: '问小咔一个问题…',
                hintStyle: GoogleFonts.dmSans(fontSize: 14, color: AppTheme.textMuted),
                filled: true,
                fillColor: AppTheme.surface2,
                contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
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
                    child: const Icon(Icons.stop, size: 18, color: Colors.white),
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
                    child: const Icon(Icons.arrow_upward, size: 18, color: Colors.white),
                  ),
                ),
        ],
      ),
    );
  }
}
