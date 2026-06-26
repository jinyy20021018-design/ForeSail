import { t, type Language } from "../i18n";

type Props = {
  fileNames: string[];
  onFileNamesChange: (fileNames: string[]) => void;
  language: Language;
};

export function FileUploadPanel({ fileNames, onFileNamesChange, language }: Props) {
  return (
    <div className="panel">
      <div className="panel-heading">
        <h2>{t(language, "uploadCaseFiles")}</h2>
        <span className="tag">{t(language, "optional")}</span>
      </div>
      <input
        type="file"
        multiple
        onChange={(event) => {
          const files = Array.from(event.target.files ?? []).map((file) => file.name);
          onFileNamesChange(files);
        }}
      />
      {fileNames.length > 0 && (
        <ul className="file-list">
          {fileNames.map((fileName) => (
            <li key={fileName}>{fileName}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
