#ifndef MESSAGETREEMODEL_H
#define MESSAGETREEMODEL_H

#include <QAbstractItemModel>
#include <QModelIndex>
#include <QVariant>
#include <QHash>

class Message;
class MessageTreeItem;

class MessageTreeModel : QAbstractItemModel
{
    Q_OBJECT

private:
    bool _readOnly;
    QHash<QPair<int, int>, MessageTreeItem*> _existingItems;

public:
    MessageTreeModel(bool readOnly);
    //MessageTreeModel(const QStringList &headers, const QString &data, QObject *parent = 0);
    virtual ~MessageTreeModel();

    QVariant data(const QModelIndex &index, int role) const;
    QVariant headerData(int section, Qt::Orientation orientation,
                        int role = Qt::DisplayRole) const;

    QModelIndex index(int row, int column,
                      const QModelIndex &parent = QModelIndex()) const;
    QModelIndex parent(const QModelIndex &index) const;

    int rowCount(const QModelIndex &parent = QModelIndex()) const;
    int columnCount(const QModelIndex &parent = QModelIndex()) const;

    Qt::ItemFlags flags(const QModelIndex &index) const;
    bool setData(const QModelIndex &index, const QVariant &value,
                 int role = Qt::EditRole);
    bool setHeaderData(int section, Qt::Orientation orientation,
                       const QVariant &value, int role = Qt::EditRole);

    bool insertColumns(int position, int columns,
                       const QModelIndex &parent = QModelIndex());
    bool removeColumns(int position, int columns,
                       const QModelIndex &parent = QModelIndex());
    bool insertRows(int position, int rows,
                    const QModelIndex &parent = QModelIndex());
    bool removeRows(int position, int rows,
                    const QModelIndex &parent = QModelIndex());

public slots:
    void onNewMessage(Message* /*msg*/)
    {
        // if not in hash table, create new item
        // new item is a "TreeItem

        // always, update item
    }
};

#endif
