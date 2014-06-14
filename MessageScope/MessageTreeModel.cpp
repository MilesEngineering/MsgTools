#include "./MessageTreeModel.h"

MessageTreeModel::MessageTreeModel(bool readOnly)
 : _readOnly(readOnly)
{

}

MessageTreeModel::~MessageTreeModel()
{
}

QVariant
MessageTreeModel::data(const QModelIndex &index, int role) const
{
    return NULL;
}

QVariant
MessageTreeModel::headerData(int section, Qt::Orientation orientation,
                    int role = Qt::DisplayRole) const
{
    return NULL;
}

QModelIndex
MessageTreeModel::index(int row, int column,
                  const QModelIndex &parent = QModelIndex()) const
{
    return NULL;
}

QModelIndex
MessageTreeModel::parent(const QModelIndex &index) const
{
    return NULL;
}

int
MessageTreeModel::rowCount(const QModelIndex &parent = QModelIndex()) const
{
    return 0;
}

int
MessageTreeModel::columnCount(const QModelIndex &parent = QModelIndex()) const
{
    return 0;
}

Qt::ItemFlags
MessageTreeModel::flags(const QModelIndex &index) const
{
    return 0;
}

bool
MessageTreeModel::setData(const QModelIndex &index, const QVariant &value,
             int role = Qt::EditRole)
{
    return false;
}

bool
MessageTreeModel::setHeaderData(int section, Qt::Orientation orientation,
                   const QVariant &value, int role = Qt::EditRole)
{
    return false;
}

bool
MessageTreeModel::insertColumns(int position, int columns,
                   const QModelIndex &parent = QModelIndex())

{
    return false;
}

bool
MessageTreeModel::removeColumns(int position, int columns,
                   const QModelIndex &parent = QModelIndex())
{
    return false;
}

bool
MessageTreeModel::insertRows(int position, int rows,
                const QModelIndex &parent = QModelIndex())
{
    return false;
}

bool
MessageTreeModel::removeRows(int position, int rows,
                const QModelIndex &parent = QModelIndex())
{
    return false;
}
