"""
Image processing module for Receipt Processing Application.

This module provides functionality for loading, validating, preprocessing,
and converting image files for optimal AI vision processing.
"""

import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ExifTags
from PIL.ExifTags import TAGS
from loguru import logger

from .config import AppSettings


class ImageFormat(Enum):
    """Supported image formats."""
    JPEG = "JPEG"
    PNG = "PNG"
    HEIC = "HEIC"
    WEBP = "WEBP"
    TIFF = "TIFF"


@dataclass
class ImageMetadata:
    """Container for image metadata and EXIF information."""
    file_path: Path
    format: str
    size: Tuple[int, int]  # (width, height)
    mode: str  # RGB, RGBA, L, etc.
    file_size: int  # bytes
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    exif_data: Dict[str, Any] = None
    has_transparency: bool = False
    color_space: str = "RGB"
    dpi: Optional[Tuple[int, int]] = None
    orientation: int = 1  # EXIF orientation


@dataclass
class ProcessingOptions:
    """Options for image preprocessing."""
    # Resize options
    max_width: int = 2048
    max_height: int = 2048
    maintain_aspect_ratio: bool = True
    
    # Enhancement options
    enhance_contrast: bool = True
    contrast_factor: float = 1.2
    enhance_sharpness: bool = True
    sharpness_factor: float = 1.1
    enhance_brightness: bool = False
    brightness_factor: float = 1.0
    
    # Quality options
    jpeg_quality: int = 95
    optimize: bool = True
    
    # Conversion options
    convert_to_rgb: bool = True
    remove_transparency: bool = True
    background_color: Tuple[int, int, int] = (255, 255, 255)  # White background
    
    # Noise reduction
    apply_noise_reduction: bool = False
    noise_reduction_strength: int = 1


class ImageProcessor:
    """Main image processing class for receipt images."""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.supported_formats = {
            '.jpg': ImageFormat.JPEG,
            '.jpeg': ImageFormat.JPEG,
            '.png': ImageFormat.PNG,
            '.heic': ImageFormat.HEIC,
            '.webp': ImageFormat.WEBP,
            '.tiff': ImageFormat.TIFF,
            '.tif': ImageFormat.TIFF,
        }
        
        logger.info("ImageProcessor initialized")
    
    def load_image(self, file_path: Union[Path, str]) -> Optional[Image.Image]:
        """
        Load an image file safely with error handling.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            PIL Image object or None if loading fails
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.error(f"Image file not found: {file_path}")
                return None
            
            # Handle HEIC files (requires pillow-heif)
            if file_path.suffix.lower() == '.heic':
                try:
                    import pillow_heif
                    pillow_heif.register_heif_opener()
                except ImportError:
                    logger.warning("pillow-heif not installed, HEIC support limited")
            
            with Image.open(file_path) as img:
                # Load the image into memory to avoid file handle issues
                img.load()
                return img.copy()
                
        except Exception as e:
            logger.error(f"Failed to load image {file_path}: {e}")
            return None
    
    def validate_image(self, image: Image.Image) -> bool:
        """
        Validate that an image is suitable for processing.
        
        Args:
            image: PIL Image object
            
        Returns:
            True if image is valid for processing
        """
        try:
            if image is None:
                return False
            
            # Check minimum size requirements
            min_width = getattr(self.settings.extraction, 'min_image_width', 100)
            min_height = getattr(self.settings.extraction, 'min_image_height', 100)
            
            width, height = image.size
            if width < min_width or height < min_height:
                logger.warning(f"Image too small: {width}x{height} (min: {min_width}x{min_height})")
                return False
            
            # Check maximum size requirements
            max_width = getattr(self.settings.extraction, 'max_image_width', 10000)
            max_height = getattr(self.settings.extraction, 'max_image_height', 10000)
            
            if width > max_width or height > max_height:
                logger.warning(f"Image too large: {width}x{height} (max: {max_width}x{max_height})")
                # Don't return False - we can resize large images
            
            # Verify image can be processed
            image.verify()
            
            return True
            
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False
    
    def extract_metadata(self, file_path: Union[Path, str], image: Optional[Image.Image] = None) -> ImageMetadata:
        """
        Extract comprehensive metadata from an image file.
        
        Args:
            file_path: Path to the image file
            image: Optional pre-loaded PIL Image
            
        Returns:
            ImageMetadata object with extracted information
        """
        file_path = Path(file_path)
        
        # Load image if not provided
        if image is None:
            image = self.load_image(file_path)
        
        if image is None:
            # Return minimal metadata for invalid images
            return ImageMetadata(
                file_path=file_path,
                format="UNKNOWN",
                size=(0, 0),
                mode="UNKNOWN",
                file_size=file_path.stat().st_size if file_path.exists() else 0
            )
        
        try:
            # Basic image information
            metadata = ImageMetadata(
                file_path=file_path,
                format=image.format or "UNKNOWN",
                size=image.size,
                mode=image.mode,
                file_size=file_path.stat().st_size if file_path.exists() else 0,
                has_transparency=image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            )
            
            # File timestamps
            if file_path.exists():
                stat = file_path.stat()
                metadata.created_date = datetime.fromtimestamp(stat.st_birthtime)
                metadata.modified_date = datetime.fromtimestamp(stat.st_mtime)
            
            # DPI information
            if hasattr(image, 'info') and 'dpi' in image.info:
                metadata.dpi = image.info['dpi']
            
            # Extract EXIF data
            metadata.exif_data = self._extract_exif_data(image)
            
            # Get orientation from EXIF
            if metadata.exif_data and 'Orientation' in metadata.exif_data:
                metadata.orientation = metadata.exif_data['Orientation']
            
            logger.debug(f"Extracted metadata for {file_path}: {metadata.format} {metadata.size}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {e}")
            return ImageMetadata(
                file_path=file_path,
                format="ERROR",
                size=(0, 0),
                mode="ERROR",
                file_size=0
            )
    
    def _extract_exif_data(self, image: Image.Image) -> Dict[str, Any]:
        """Extract EXIF data from an image."""
        exif_data = {}
        
        try:
            if hasattr(image, '_getexif'):
                exif = image._getexif()
                if exif is not None:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value
            
            # Also try the newer method
            if hasattr(image, 'getexif'):
                exif = image.getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value
                        
        except Exception as e:
            logger.debug(f"EXIF extraction failed: {e}")
        
        return exif_data
    
    def preprocess_image(
        self, 
        image: Image.Image, 
        options: Optional[ProcessingOptions] = None
    ) -> Image.Image:
        """
        Preprocess an image for optimal AI vision processing.
        
        Args:
            image: PIL Image object
            options: Processing options
            
        Returns:
            Preprocessed PIL Image object
        """
        if options is None:
            options = ProcessingOptions()
        
        try:
            processed_image = image.copy()
            
            # Handle orientation based on EXIF data
            processed_image = ImageOps.exif_transpose(processed_image)
            
            # Convert to RGB if needed
            if options.convert_to_rgb and processed_image.mode != 'RGB':
                if processed_image.mode == 'RGBA' and options.remove_transparency:
                    # Create white background for transparency
                    background = Image.new('RGB', processed_image.size, options.background_color)
                    background.paste(processed_image, mask=processed_image.split()[-1])
                    processed_image = background
                else:
                    processed_image = processed_image.convert('RGB')
            
            # Resize if needed
            processed_image = self._resize_image(processed_image, options)
            
            # Apply enhancements
            if options.enhance_contrast:
                enhancer = ImageEnhance.Contrast(processed_image)
                processed_image = enhancer.enhance(options.contrast_factor)
            
            if options.enhance_sharpness:
                enhancer = ImageEnhance.Sharpness(processed_image)
                processed_image = enhancer.enhance(options.sharpness_factor)
            
            if options.enhance_brightness and options.brightness_factor != 1.0:
                enhancer = ImageEnhance.Brightness(processed_image)
                processed_image = enhancer.enhance(options.brightness_factor)
            
            # Apply noise reduction
            if options.apply_noise_reduction:
                processed_image = self._apply_noise_reduction(processed_image, options.noise_reduction_strength)
            
            logger.debug(f"Preprocessed image: {image.size} -> {processed_image.size}")
            return processed_image
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return image  # Return original image on failure
    
    def _resize_image(self, image: Image.Image, options: ProcessingOptions) -> Image.Image:
        """Resize image according to processing options."""
        width, height = image.size
        
        # Check if resizing is needed
        if width <= options.max_width and height <= options.max_height:
            return image
        
        if options.maintain_aspect_ratio:
            # Calculate scaling factor
            scale_factor = min(
                options.max_width / width,
                options.max_height / height
            )
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
        else:
            new_width = min(width, options.max_width)
            new_height = min(height, options.max_height)
        
        # Use high-quality resampling
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _apply_noise_reduction(self, image: Image.Image, strength: int) -> Image.Image:
        """Apply noise reduction filter."""
        try:
            if strength == 1:
                return image.filter(ImageFilter.SMOOTH)
            elif strength == 2:
                return image.filter(ImageFilter.SMOOTH_MORE)
            elif strength >= 3:
                # Apply multiple passes for stronger noise reduction
                filtered_image = image
                for _ in range(min(strength - 2, 3)):
                    filtered_image = filtered_image.filter(ImageFilter.SMOOTH)
                return filtered_image
            else:
                return image
        except Exception as e:
            logger.error(f"Noise reduction failed: {e}")
            return image
    
    def convert_format(
        self, 
        image: Image.Image, 
        target_format: ImageFormat,
        quality: int = 95
    ) -> bytes:
        """
        Convert image to specified format and return as bytes.
        
        Args:
            image: PIL Image object
            target_format: Target format
            quality: JPEG quality (1-100)
            
        Returns:
            Image data as bytes
        """
        try:
            output = io.BytesIO()
            
            # Ensure RGB mode for JPEG
            if target_format == ImageFormat.JPEG and image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save with appropriate options
            save_options = {'format': target_format.value}
            
            if target_format == ImageFormat.JPEG:
                save_options.update({
                    'quality': quality,
                    'optimize': True,
                    'progressive': True
                })
            elif target_format == ImageFormat.PNG:
                save_options.update({
                    'optimize': True,
                    'compress_level': 6
                })
            
            image.save(output, **save_options)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Format conversion failed: {e}")
            raise
    
    def save_processed_image(
        self, 
        image: Image.Image, 
        output_path: Union[Path, str],
        options: Optional[ProcessingOptions] = None
    ) -> bool:
        """
        Save a processed image to disk.
        
        Args:
            image: PIL Image object
            output_path: Output file path
            options: Processing options for save quality
            
        Returns:
            True if save was successful
        """
        try:
            output_path = Path(output_path)
            options = options or ProcessingOptions()
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine format from file extension
            ext = output_path.suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                image.save(
                    output_path,
                    'JPEG',
                    quality=options.jpeg_quality,
                    optimize=options.optimize
                )
            elif ext == '.png':
                image.save(output_path, 'PNG', optimize=options.optimize)
            else:
                image.save(output_path)
            
            logger.info(f"Saved processed image: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save image to {output_path}: {e}")
            return False
    
    def get_optimal_processing_options(self, metadata: ImageMetadata) -> ProcessingOptions:
        """
        Get optimal processing options based on image metadata.
        
        Args:
            metadata: Image metadata
            
        Returns:
            Optimized ProcessingOptions
        """
        options = ProcessingOptions()
        
        width, height = metadata.size
        
        # Adjust max size based on original image size
        if width > 4000 or height > 4000:
            # Very large images - more aggressive resizing
            options.max_width = 2048
            options.max_height = 2048
        elif width > 2000 or height > 2000:
            # Large images - moderate resizing
            options.max_width = 1600
            options.max_height = 1600
        else:
            # Smaller images - minimal resizing
            options.max_width = max(width, 1200)
            options.max_height = max(height, 1200)
        
        # Adjust enhancement based on image characteristics
        if metadata.format == 'JPEG':
            # JPEG images may benefit from less sharpening
            options.sharpness_factor = 1.05
        
        # Adjust quality based on original format
        if metadata.format in ['PNG', 'TIFF']:
            options.jpeg_quality = 98  # Higher quality for converted lossless formats
        
        return options


# Convenience functions
def load_and_validate_image(file_path: Union[Path, str], settings: AppSettings) -> Optional[Image.Image]:
    """Load and validate an image file."""
    processor = ImageProcessor(settings)
    image = processor.load_image(file_path)
    if image and processor.validate_image(image):
        return image
    return None


def preprocess_receipt_image(
    image: Image.Image, 
    settings: AppSettings,
    custom_options: Optional[ProcessingOptions] = None
) -> Image.Image:
    """Preprocess a receipt image for AI processing."""
    processor = ImageProcessor(settings)
    return processor.preprocess_image(image, custom_options)


def extract_image_metadata(file_path: Union[Path, str], settings: AppSettings) -> ImageMetadata:
    """Extract metadata from an image file."""
    processor = ImageProcessor(settings)
    return processor.extract_metadata(file_path)
