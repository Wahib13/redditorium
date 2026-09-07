import './SourceAvatar.css';

interface Props {
  name: string;
  iconUrl: string | null;
  /** s = top bar (26px), m = article row (40px), l = profile header (64px) */
  size: 's' | 'm' | 'l';
}

/** Round profile-picture style logo for a source; falls back to the initial letter. */
export function SourceAvatar({ name, iconUrl, size }: Props) {
  return (
    <span className={`avatar avatar--${size}`} aria-hidden="true">
      {iconUrl ? <img src={iconUrl} alt="" loading="lazy" /> : name.charAt(0).toUpperCase()}
    </span>
  );
}
