import Foundation

//TODO need big and little endian version!
extension NSMutableData
{
    public func SetField<AccessType>(offset: Int, value: AccessType)
    {
        // need to swap byte order if endian doesn't match
        var valueCopy = value;
        withUnsafePointer(to: &valueCopy)
        {        
            self.replaceBytes(in: NSRange(location: offset, length: MemoryLayout<AccessType>.size), withBytes: $0);
        }
    }
    public func GetField<AccessType>(offset: Int) -> AccessType
    {
        let valuePtr = UnsafeMutablePointer<AccessType>.allocate(capacity: 1);
        // need to swap byte order if endian doesn't match
        self.getBytes(valuePtr, range: NSRange(location: offset, length: MemoryLayout<AccessType>.size));
        return valuePtr.pointee;
    }
};
