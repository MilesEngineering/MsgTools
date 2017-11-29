package msgtools.milesengineering.androidserver;

import android.content.Context;
import android.graphics.Typeface;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseExpandableListAdapter;
import android.widget.TextView;

import java.util.HashMap;
import java.util.List;

/**
 * Expandable list adapter for our data set.  Credit where due: Adapted from a tutorial
 * on Android hive at https://www.androidhive.info/2013/07/android-expandable-list-view-tutorial/
 */
public class AppExpandableListAdapter extends BaseExpandableListAdapter {

    private Context m_Context;
    private List<String> m_ListHeaders; // header titles
    // child data in format of header title, child title
    private HashMap<String, List<String>> m_ListData;

    public AppExpandableListAdapter(Context context, List<String> listHeaders,
                                    HashMap<String, List<String>> listData) {
        this.m_Context = context;
        this.m_ListHeaders = listHeaders;
        this.m_ListData = listData;
    }

    @Override
    public Object getChild(int groupPosition, int childPosititon) {
        return this.m_ListData.get(this.m_ListHeaders.get(groupPosition))
                .get(childPosititon);
    }

    @Override
    public long getChildId(int groupPosition, int childPosition) {
        return childPosition;
    }

    @Override
    public View getChildView(int groupPosition, final int childPosition,
                             boolean isLastChild, View convertView, ViewGroup parent) {

        final String childText = (String) getChild(groupPosition, childPosition);

        if (convertView == null) {
            LayoutInflater infalInflater = (LayoutInflater) this.m_Context
                    .getSystemService(Context.LAYOUT_INFLATER_SERVICE);

            convertView = infalInflater.inflate(R.layout.list_item, null);
        }

        TextView txtListChild = (TextView) convertView
                .findViewById(R.id.lblListItem);

        txtListChild.setText(childText);
        return convertView;
    }

    @Override
    public int getChildrenCount(int groupPosition) {
        return this.m_ListData.get(this.m_ListHeaders.get(groupPosition))
                .size();
    }

    @Override
    public Object getGroup(int groupPosition) {
        return this.m_ListHeaders.get(groupPosition);
    }

    @Override
    public int getGroupCount() {
        return this.m_ListHeaders.size();
    }

    @Override
    public long getGroupId(int groupPosition) {
        return groupPosition;
    }

    @Override
    public View getGroupView(int groupPosition, boolean isExpanded,
                             View convertView, ViewGroup parent) {
        String headerTitle = (String) getGroup(groupPosition);
        if (convertView == null) {
            LayoutInflater infalInflater = (LayoutInflater) this.m_Context
                    .getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            convertView = infalInflater.inflate(R.layout.list_header, null);
        }

        TextView lblListHeader = (TextView) convertView
                .findViewById(R.id.list_header);
        lblListHeader.setTypeface(null, Typeface.BOLD);
        lblListHeader.setText(headerTitle);

        return convertView;
    }

    @Override
    public boolean hasStableIds() {
        return false;
    }

    @Override
    public boolean isChildSelectable(int groupPosition, int childPosition) {
        return true;
    }
}