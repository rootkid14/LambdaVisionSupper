import { useTagDb } from "../UIEngineStores/GlobalTagsStore";

export const useTagValue = <T = any>(tagName: string) : T | undefined => {
    return useTagDb((state) => state.tags[tagName] as T);
};

export const useWriteTag = () => {
    return useTagDb((state) => state.writeTag);
};