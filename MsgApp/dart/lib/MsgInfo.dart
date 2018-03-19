import 'dart:collection';
import 'package:msgtools/FieldInfo.dart';

class MsgInfo
{
    const MsgInfo(this.id, this.name, this.description, this.size, this.fields);

    final int              id;
    final String           name;
    final String           description;
    final int              size;
    final LinkedHashMap<String, FieldInfo> fields;
}
