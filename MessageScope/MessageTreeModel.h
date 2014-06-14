#ifndef MESSAGETREEMODEL_H
#define MESSAGETREEMODEL_H

#include <QAbstractItemModel>
#include <QModelIndex>
#include <QVariant>
#include <QHash>

template class QTuple<T1, T2>
{
private:
    T1 _first;
    T2 _second;

public:
    QTuple<T1, T2>(T1 first, T2 second)
    {
        _first = first;
        _second = second;
    }

    T1 first() { return _first; }
    T2 second() { return _second; }

   inline bool operator==(const T &e1, const T &e2)
    {
        return e1.name() == e2.name()
               && e1.dateOfBirth() == e2.dateOfBirth();
    }

    inline uint qHash(const Employee &key, uint seed)
    {
        return qHash(key.name(), seed) ^ key.dateOfBirth().day();
    }

};

class MessagesTreeModel : QAbstractItemModel
{
private:
    bool readOnly;
    QHash<QTuple<int, int>, MessageTreeItem*> _existingItems;

public:
    MessagesTreeModel(bool readOnly)
      : _readOnly(readOnly)
    {
    }

    SLOT void onNewMessage(Message* msg)
    {
        // if not in hash table, create new item
        // new item is a "TreeItem

        // always, update item
    }
};

#endif MESSAGETREEMODEL_H
