import 'dart:io';

bool isSocketLikeError(Object error) {
  return error is SocketException;
}
